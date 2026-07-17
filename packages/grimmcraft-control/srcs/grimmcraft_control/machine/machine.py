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


class MachineBuilder(Generic[Ctx]):
    """A fluent DSL for declaring a :class:`Machine`, validated at :meth:`build`."""

    def __init__(self, context: Ctx, *, name: str = "machine") -> None:
        self._context = context
        self._name = name
        self._entity: str | None = None
        self._states: dict[str, State] = {}
        self._transitions: list[Transition] = []
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
        """Declare a state with optional final flag and enter/exit/cycle commands."""
        self._states[name] = State(
            name, final, tuple(enter), tuple(exit), tuple(cycle)
        )
        return self

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
        """Declare a ``(source, event) -> to`` edge with optional guard/effects."""
        self._transitions.append(
            Transition(source, event, to, guard, action, tuple(commands), condition)
        )
        return self

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

        seen_unguarded: set[tuple[str, str]] = set()
        for t in self._transitions:
            for role, ref in (("source", t.source), ("target", t.target)):
                if ref not in self._states:
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
            dict(self._states),
            list(self._transitions),
            self._initial,
            self._context,
            entity=self._entity,
        )
