"""The :class:`Machine` runtime plus the fluent :class:`MachineBuilder`.

The machine is deterministic and side-effect-free: :meth:`Machine.dispatch`
evaluates guards, collects the commands from ``on_exit`` → action → ``on_enter``,
advances ``current_state`` and returns a :class:`Result`.  It never performs I/O;
a :class:`~.command.CommandBus` does that at the edge.  A machine is generic over
its context type ``Ctx``.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Generic, TypeVar

from grimmcraft_control.machine.command import Command
from grimmcraft_control.machine.errors import (
    GuardError,
    InvalidTransition,
    MachineBuildError,
)
from grimmcraft_control.machine.event import Event
from grimmcraft_control.machine.result import Result
from grimmcraft_control.machine.state import State
from grimmcraft_control.machine.transition import Action, Condition, Guard, Transition
from grimmcraft_control.machine.vocabulary import ConditionName

Ctx = TypeVar("Ctx")

#: The scoreboard objective every machine's current state is tracked in.
STATE_OBJECTIVE = "grimmcraft_state"

#: Event type for *automatic* transitions evaluated once per tick, after a
#: state's cycle commands.  Their guard/condition decides whether they fire.
TICK_EVENT = "tick"


class Machine(Generic[Ctx]):
    """A live state machine over a context ``Ctx``.

    Built via :class:`MachineBuilder`.  The definition (states, transitions) is
    immutable; only :attr:`current_state`, :attr:`context` and :attr:`history`
    change at runtime.  ``name`` doubles as the entry under the
    ``grimmcraft_state`` scoreboard objective, and ``entity`` optionally binds
    the machine to a domain entity/block id.
    """

    def __init__(
        self,
        name: str,
        states: dict[str, State],
        transitions: list[Transition],
        initial: str,
        context: Ctx,
        *,
        entity: str | None = None,
        strict: bool = False,
    ) -> None:
        self.name = name
        self.states = states
        self.transitions = transitions
        self.initial = initial
        self.context = context
        self.entity = entity
        self.strict = strict
        self.current_state = initial
        self.history: list[str] = [initial]
        # (source, event_type) -> transitions, in declaration order (first match).
        self._index: dict[tuple[str, str], list[Transition]] = {}
        for transition in transitions:
            self._index.setdefault((transition.source, transition.event), []).append(
                transition
            )

    @property
    def state(self) -> State:
        """The :class:`State` object the machine is currently in."""
        return self.states[self.current_state]

    def transitions_from(self, state: str) -> list[Transition]:
        """Every transition whose source is ``state`` (the compiler lowers these)."""
        return [t for t in self.transitions if t.source == state]

    def can(self, event: Event) -> bool:
        """Whether ``event`` would currently fire a transition (guards included)."""
        return self._match(event) is not None

    def dispatch(self, event: Event) -> Result:
        """Evaluate ``event`` and, if a transition fires, advance state.

        Returns :meth:`Result.transitioned` on success (with the collected
        commands) or :meth:`Result.rejected` when nothing matches.  With
        ``strict=True`` a non-match raises :class:`InvalidTransition` instead.
        """
        transition = self._match(event)
        if transition is None:
            if self.strict:
                raise InvalidTransition(
                    f"{self.name}: no transition from '{self.current_state}' "
                    f"on event '{event.type}'"
                )
            return Result.rejected(
                event,
                self.current_state,
                f"no transition from '{self.current_state}' on '{event.type}'",
            )

        source = self.states[self.current_state]
        target = self.states[transition.target]
        commands: list[Command] = []
        commands += source.on_exit(self.context, event)
        commands += transition.run_action(self.context, event)
        commands += target.on_enter(self.context, event)

        self.current_state = transition.target
        self.history.append(transition.target)
        return Result.transitioned(event, source.name, target.name, commands)

    def _match(self, event: Event) -> Transition | None:
        """First transition from the current state whose guard passes."""
        for transition in self._index.get((self.current_state, event.type), []):
            if transition.guard is None:
                return transition
            try:
                if transition.guard(self.context, event):
                    return transition
            except Exception as exc:  # noqa: BLE001 - re-raised as a clear error
                raise GuardError(
                    f"{self.name}: guard for '{transition.source}'->"
                    f"'{transition.target}' raised: {exc}"
                ) from exc
        return None


class StateDraft:
    """A state under construction — add its commands one method call at a time.

    Returned by :meth:`MachineBuilder.add_state`. ``on_enter`` / ``on_exit`` /
    ``on_cycle`` each append one or more :class:`Command`\\ s (build them with the
    constructors in :mod:`grimmcraft_control.machine.effects`), so a beginner
    writes one readable line per effect instead of nesting tuples of ``Command``.
    """

    def __init__(self, name: str, *, final: bool = False) -> None:
        self.name = name
        self._final = final
        self._enter: list[Command] = []
        self._exit: list[Command] = []
        self._cycle: list[Command] = []

    def final(self) -> StateDraft:
        """Mark this state as terminal."""
        self._final = True
        return self

    def on_enter(self, *commands: Command) -> StateDraft:
        """Add command(s) to run once when the machine enters this state."""
        self._enter.extend(commands)
        return self

    def on_exit(self, *commands: Command) -> StateDraft:
        """Add command(s) to run once when the machine leaves this state."""
        self._exit.extend(commands)
        return self

    def on_cycle(self, *commands: Command) -> StateDraft:
        """Add command(s) to run every tick while in this state."""
        self._cycle.extend(commands)
        return self

    def to_state(self) -> State:
        """Freeze this draft into an immutable :class:`State`."""
        return State(
            self.name, self._final, tuple(self._enter), tuple(self._exit),
            tuple(self._cycle),
        )


class TransitionDraft:
    """A transition under construction (from :meth:`MachineBuilder.add_transition`)."""

    def __init__(self, source: str, event: str, target: str) -> None:
        self.source = source
        self.event = event
        self.target = target
        self._guard: Guard | None = None
        self._condition: Condition | None = None
        self._commands: list[Command] = []

    def do(self, *commands: Command) -> TransitionDraft:
        """Add command(s) this transition runs when it fires."""
        self._commands.extend(commands)
        return self

    def when_score(self, objective: str, entry: str, value: int) -> TransitionDraft:
        """Fire only when ``entry``'s ``objective`` score equals ``value``
        (a declarative guard the compiler can lower)."""
        self._condition = Condition(
            ConditionName.SCORE_MATCHES,
            {"objective": objective, "entry": entry, "value": value},
        )
        return self

    def guarded_by(self, guard: Guard) -> TransitionDraft:
        """Fire only when the runtime ``guard`` predicate returns True."""
        self._guard = guard
        return self

    def to_transition(self) -> Transition:
        """Freeze this draft into an immutable :class:`Transition`."""
        return Transition(
            self.source, self.event, self.target, self._guard, None,
            tuple(self._commands), self._condition,
        )


class MachineBuilder(Generic[Ctx]):
    """A DSL for declaring a :class:`Machine`, validated at :meth:`build`.

    Two mixable styles:

    * **Compact** — pass everything in one call: ``.state("ON", enter=(...))``
      and ``.transition("A", "go", to="B", commands=(...))``. These return the
      builder, so they chain.
    * **Step by step** — ``.add_state("ON")`` / ``.add_transition("A", "go",
      to="B")`` return a :class:`StateDraft` / :class:`TransitionDraft` you
      configure with one method call per command. Friendliest for beginners and
      pairs with the constructors in :mod:`grimmcraft_control.machine.effects`.
    """

    def __init__(self, context: Ctx, *, name: str = "machine") -> None:
        self._context = context
        self._name = name
        self._entity: str | None = None
        self._states: dict[str, StateDraft] = {}
        self._transitions: list[Transition] = []
        self._transition_drafts: list[TransitionDraft] = []
        self._initial: str | None = None

    def named(self, name: str) -> MachineBuilder[Ctx]:
        """Set the machine name (its ``grimmcraft_state`` scoreboard entry)."""
        self._name = name
        return self

    def for_entity(self, entity: str) -> MachineBuilder[Ctx]:
        """Bind the machine to a domain entity/block id (optional)."""
        self._entity = entity
        return self

    def state(
        self,
        name: str,
        *,
        final: bool = False,
        enter: Iterable[Command] = (),
        exit: Iterable[Command] = (),
        cycle: Iterable[Command] = (),
    ) -> MachineBuilder[Ctx]:
        """Declare a state and its commands in one call; returns the builder."""
        draft = StateDraft(name, final=final)
        draft.on_enter(*enter)
        draft.on_exit(*exit)
        draft.on_cycle(*cycle)
        self._states[name] = draft
        return self

    def add_state(self, name: str, *, final: bool = False) -> StateDraft:
        """Declare a state and return a :class:`StateDraft` to add commands to one
        method call at a time (the beginner-friendly style)."""
        draft = StateDraft(name, final=final)
        self._states[name] = draft
        return draft

    def transition(
        self,
        source: str,
        event: str,
        *,
        to: str,
        guard: Guard | None = None,
        action: Action | None = None,
        commands: Iterable[Command] = (),
        condition: Condition | None = None,
    ) -> MachineBuilder[Ctx]:
        """Declare a ``(source, event) -> to`` edge in one call; returns the builder."""
        self._transitions.append(
            Transition(source, event, to, guard, action, tuple(commands), condition)
        )
        return self

    def add_transition(self, source: str, event: str, *, to: str) -> TransitionDraft:
        """Declare an edge and return a :class:`TransitionDraft` to configure its
        commands and guard step by step."""
        draft = TransitionDraft(source, event, to)
        self._transition_drafts.append(draft)
        return draft

    def initial(self, name: str) -> MachineBuilder[Ctx]:
        """Choose the initial state."""
        self._initial = name
        return self

    def build(self) -> Machine[Ctx]:
        """Validate the definition and return an immutable :class:`Machine`.

        Rejects: no/unknown initial state, transitions referencing unknown
        states, and duplicate *unguarded* transitions on the same ``(source,
        event)`` (which would be ambiguous).
        """
        if self._initial is None:
            raise MachineBuildError(f"machine '{self._name}' has no initial state")
        if self._initial not in self._states:
            raise MachineBuildError(
                f"initial state '{self._initial}' is not a declared state"
            )

        states = {name: draft.to_state() for name, draft in self._states.items()}
        transitions = list(self._transitions)
        transitions += [draft.to_transition() for draft in self._transition_drafts]

        seen_unguarded: set[tuple[str, str]] = set()
        for t in transitions:
            for role, ref in (("source", t.source), ("target", t.target)):
                if ref not in states:
                    raise MachineBuildError(
                        f"transition {t.source}--{t.event}-->{t.target} references "
                        f"unknown {role} state '{ref}'"
                    )
            if t.guard is None and t.condition is None:
                key = (t.source, t.event)
                if key in seen_unguarded:
                    raise MachineBuildError(
                        f"ambiguous transitions from '{t.source}' on '{t.event}': "
                        "add a guard to disambiguate"
                    )
                seen_unguarded.add(key)

        return Machine(
            self._name,
            states,
            transitions,
            self._initial,
            self._context,
            entity=self._entity,
        )
