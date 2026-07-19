"""Level 2 — reconstruct :class:`Machine`\\ s from the IR, inverting ``lower.py``.

Lowering is lossy in one specific way, and understanding it explains this whole
module.  A transition function is emitted as::

    <source state's exit commands>
    <the transition's own commands>
    scoreboard players set <machine> grimmcraft_state <target index>
    <target state's enter commands>

The state write is an unambiguous fence: everything after it is the *target's*
enter block, recoverable exactly.  Everything before it is the concatenation of
two lists whose boundary is **not** recorded.  We recover it the only way the
data allows — a state's exit commands are the part shared by *every* transition
leaving it, so the longest common prefix across those transitions is the exit
block and each remainder is that transition's own commands.

With a single outgoing transition the split is genuinely undecidable; we then
attribute everything to the state's exit and say so (``GD2004``).  Either
attribution re-lowers to identical bytes, so the round-trip still holds — what
is lost is only *which name* the author gave the commands, not their behaviour.

Names survive because the compiler writes them into comments: ``# states: OFF=0,
ON=1`` in ``init`` recovers the original casing that the path slug destroyed, and
``# OFF --pull--> ON`` on each transition function recovers source, event and
target verbatim.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from grimmcraft_compiler.ir import Datapack, Function
from grimmcraft_control.machine import (
    STATE_OBJECTIVE,
    Command,
    Condition,
    ConditionName,
    Machine,
    MachineBuilder,
)
from grimmcraft_decompiler.diagnostics import Codes, DiagnosticBag

#: ``# states: OFF=0, ON=1`` — the index map lowering writes into ``init``.
_STATES_COMMENT = re.compile(r"^states:\s*(?P<body>.+)$")

#: One ``NAME=INDEX`` pair inside that comment.
_STATE_PAIR = re.compile(r"^(?P<name>.+?)=(?P<index>\d+)$")

#: ``# OFF --pull--> ON`` — the comment on each ``do_…`` transition function.
_TRANSITION_COMMENT = re.compile(
    r"^(?P<source>.+?) --(?P<event>.+?)--> (?P<target>.+)$"
)

#: ``# Tick while in ON`` — the comment on each ``tick_<state>`` function.
_TICK_COMMENT = re.compile(r"^Tick while in (?P<state>.+)$")


@dataclass(slots=True)
class _TransitionFacts:
    """What the IR tells us about one transition, before states are assembled."""

    source: str
    event: str
    target: str
    #: Commands before the state write — exit + the transition's own, unsplit.
    prefix: list[Command]
    #: Commands after the state write — the target state's enter block.
    enter: list[Command]
    condition: Condition | None = None
    #: The transition's own commands, once the exit prefix has been removed.
    commands: list[Command] = field(default_factory=list)


class NotLiftable(Exception):
    """Raised when the IR does not follow the grimmcraft lowering convention."""


def _comment_text(command: Command) -> str | None:
    """The text of a ``comment`` command, or ``None`` for anything else."""
    if command.name != "comment":
        return None
    text = command.payload.get("text")
    return text if isinstance(text, str) else None


def _find_comment(function: Function, pattern: re.Pattern[str]) -> re.Match[str] | None:
    """The first comment in ``function`` matching ``pattern``."""
    for command in function.commands:
        text = _comment_text(command)
        if text is not None and (match := pattern.match(text)) is not None:
            return match
    return None


def _is_state_write(command: Command, machine: str) -> bool:
    """Whether ``command`` is this machine's ``grimmcraft_state`` write."""
    return (
        command.name == "scoreboard_set"
        and command.payload.get("objective") == STATE_OBJECTIVE
        and command.payload.get("entry") == machine
    )


def _body(function: Function) -> list[Command]:
    """A function's commands with its leading header comment dropped.

    Lowering writes the header via :attr:`Function.comment`; the IR lifter keeps
    it as a leading ``comment`` command instead. Both render identically, so the
    lifter strips whichever it finds.
    """
    commands = list(function.commands)
    if commands and _comment_text(commands[0]) is not None:
        return commands[1:]
    return commands


def _innermost(command: Command) -> Command:
    """Follow ``execute_if_score`` wrappers down to the command they run."""
    current = command
    while current.name == "execute_if_score":
        run = current.payload.get("run")
        if not isinstance(run, Command):
            return current
        current = run
    return current


def _guard_chain(command: Command) -> list[Command]:
    """Every ``execute_if_score`` wrapper around a command, outermost first."""
    chain: list[Command] = []
    current = command
    while current.name == "execute_if_score":
        chain.append(current)
        run = current.payload.get("run")
        if not isinstance(run, Command):
            break
        current = run
    return chain


def _call_ref(command: Command) -> str | None:
    """The ``ns:path`` target of a ``call``, or ``None``."""
    if command.name != "call":
        return None
    ref = command.payload.get("ref")
    return ref if isinstance(ref, str) else None


def _condition_from(command: Command) -> Condition:
    """Turn a non-state ``execute_if_score`` guard into a declarative Condition."""
    return Condition(
        ConditionName.SCORE_MATCHES,
        {
            "objective": command.payload["objective"],
            "entry": command.payload["entry"],
            "value": command.payload["value"],
        },
    )


def _common_prefix(sequences: list[list[Command]]) -> list[Command]:
    """The longest list of commands every sequence starts with."""
    if not sequences:
        return []
    prefix: list[Command] = []
    for candidates in zip(*sequences, strict=False):
        first = candidates[0]
        if any(other != first for other in candidates[1:]):
            break
        prefix.append(first)
    return prefix


class _MachineLifter:
    """Reconstructs one machine from the functions under ``<ns>:<name>/``."""

    def __init__(
        self, pack: Datapack, name: str, bag: DiagnosticBag
    ) -> None:
        self.pack = pack
        self.name = name
        self.bag = bag
        self.ns = pack.namespace
        self.functions = {str(function.id): function for function in pack.functions}
        self.source = f"{self.ns}:{name}"

    def fn(self, path: str) -> Function | None:
        return self.functions.get(f"{self.ns}:{self.name}/{path}")

    def lift(self) -> Machine[Any]:
        """Rebuild the machine, or raise :class:`NotLiftable`."""
        init = self.fn("init")
        if init is None:
            raise NotLiftable(f"no '{self.name}/init' function")

        index_to_state = self._read_state_index(init)
        initial, initial_enter = self._read_init(init, index_to_state)

        facts = self._read_transitions(index_to_state)
        enters = self._collect_enters(facts, initial, initial_enter)
        exits = self._split_exits(facts)
        cycles = self._read_cycles(index_to_state, facts)

        return self._build(index_to_state, initial, facts, enters, exits, cycles)

    # --- init ----------------------------------------------------------------
    def _read_state_index(self, init: Function) -> dict[int, str]:
        """Recover ``index -> state name`` from the ``# states: …`` comment."""
        match = _find_comment(init, _STATES_COMMENT)
        if match is None:
            raise NotLiftable(
                f"'{self.name}/init' has no '# states: …' comment, so the state "
                "names and their scoreboard indices cannot be recovered"
            )
        mapping: dict[int, str] = {}
        for chunk in match.group("body").split(","):
            pair = _STATE_PAIR.match(chunk.strip())
            if pair is None:
                continue
            index = int(pair.group("index"))
            name = pair.group("name")
            if index in mapping:
                self.bag.emit(
                    Codes.AMBIGUOUS_RECONSTRUCTION,
                    f"states '{mapping[index]}' and '{name}' both claim index "
                    f"{index} in machine '{self.name}'; keeping '{mapping[index]}'",
                    hint="two states cannot share a scoreboard value — the pack "
                    "may have been edited by hand",
                    source=self.source,
                )
                continue
            mapping[index] = name
        if not mapping:
            raise NotLiftable(f"'{self.name}/init' lists no states")
        return mapping

    def _read_init(
        self, init: Function, index_to_state: dict[int, str]
    ) -> tuple[str, list[Command]]:
        """The initial state's name and its enter block."""
        commands = _body(init)
        # Drop the '# states: …' comment, which _body's header strip leaves.
        commands = [
            command
            for command in commands
            if _comment_text(command) is None
            or _STATES_COMMENT.match(_comment_text(command) or "") is None
        ]
        for position, command in enumerate(commands):
            if _is_state_write(command, self.name):
                value = command.payload.get("value")
                state = index_to_state.get(int(value)) if isinstance(value, int) else None
                if state is None:
                    raise NotLiftable(
                        f"'{self.name}/init' sets state index {value}, which the "
                        "'# states:' comment does not name"
                    )
                return state, commands[position + 1 :]
        raise NotLiftable(
            f"'{self.name}/init' never sets the '{STATE_OBJECTIVE}' score, so the "
            "initial state is unknown"
        )

    # --- transitions ---------------------------------------------------------
    def _read_transitions(self, index_to_state: dict[int, str]) -> list[_TransitionFacts]:
        """Every transition, discovered through the event and tick dispatchers.

        Dispatchers (not the ``do_…`` files) are the source of truth for
        *ordering* and for the guard conditions, which live at the call site.
        """
        facts: list[_TransitionFacts] = []
        seen: set[str] = set()

        prefix = f"{self.ns}:{self.name}/"
        dispatchers = sorted(
            (path for path in self.functions if path.startswith(f"{prefix}on_")),
        )
        for path in dispatchers:
            for entry in self._read_dispatch_entries(self.functions[path], index_to_state):
                facts.append(entry)
                seen.add(entry.source + "\0" + entry.event + "\0" + entry.target)

        facts.extend(self._read_tick_transitions(index_to_state))

        defined = {
            path
            for path in self.functions
            if path.startswith(f"{prefix}do_")
        }
        reached = {f"{prefix}{self._fn_name(fact)}" for fact in facts}
        for orphan in sorted(defined - reached):
            self.bag.emit(
                Codes.AMBIGUOUS_RECONSTRUCTION,
                f"transition function '{orphan}' is never dispatched, so it cannot "
                "be attributed to an event; it is dropped from the machine",
                hint="unreachable transition functions have no effect in game either",
                source=self.source,
            )
        return facts

    @staticmethod
    def _fn_name(fact: _TransitionFacts) -> str:
        """The ``do_…`` basename lowering would give this transition."""
        from grimmcraft_compiler.lower import _transition_fn_name
        from grimmcraft_control.machine import Transition

        return _transition_fn_name(
            Transition(fact.source, fact.event, fact.target)
        )

    def _read_dispatch_entries(
        self, dispatcher: Function, index_to_state: dict[int, str]
    ) -> list[_TransitionFacts]:
        """Parse one ``on_<event>`` function into transition facts, in file order."""
        entries: list[_TransitionFacts] = []
        for command in _body(dispatcher):
            chain = _guard_chain(command)
            call = _call_ref(_innermost(command))
            if not chain or call is None:
                continue
            state_guards = [
                guard
                for guard in chain
                if guard.payload.get("objective") == STATE_OBJECTIVE
                and guard.payload.get("entry") == self.name
            ]
            if not state_guards:
                continue
            source = index_to_state.get(int(state_guards[0].payload["value"]))
            if source is None:
                continue
            others = [guard for guard in chain if guard not in state_guards]
            condition = _condition_from(others[0]) if others else None
            fact = self._facts_for(call, source, condition)
            if fact is not None:
                entries.append(fact)
        return entries

    def _read_tick_transitions(
        self, index_to_state: dict[int, str]
    ) -> list[_TransitionFacts]:
        """Automatic (``tick``) transitions, read from each ``tick_<state>`` body."""
        entries: list[_TransitionFacts] = []
        for state in index_to_state.values():
            function = self._tick_function(state)
            if function is None:
                continue
            for command in self._auto_calls(function):
                chain = _guard_chain(command)
                call = _call_ref(_innermost(command))
                if call is None:
                    continue
                condition = _condition_from(chain[0]) if chain else None
                fact = self._facts_for(call, state, condition)
                if fact is not None:
                    entries.append(fact)
        return entries

    def _tick_function(self, state: str) -> Function | None:
        """The ``tick_<state>`` function, matched by its ``# Tick while in …`` comment.

        The path uses a slug, which lower-cases the state name; the comment
        carries the original casing, so it is the reliable key.
        """
        from grimmcraft_compiler.lower import slug

        function = self.fn(f"tick_{slug(state)}")
        if function is None:
            return None
        match = _find_comment(function, _TICK_COMMENT)
        if match is not None and match.group("state") != state:
            return None
        return function

    def _auto_calls(self, function: Function) -> list[Command]:
        """The trailing commands of a tick body that dispatch a transition.

        A tick body is ``<cycle commands>`` followed by ``<auto transitions>``.
        Scanning from the end distinguishes them: an auto transition's innermost
        command is a ``call`` to one of *this machine's* ``do_…`` functions,
        which a cycle effect never is.
        """
        commands = _body(function)
        prefix = f"{self.ns}:{self.name}/do_"
        cut = len(commands)
        for position in range(len(commands) - 1, -1, -1):
            ref = _call_ref(_innermost(commands[position]))
            if ref is None or not ref.startswith(prefix):
                break
            cut = position
        return commands[cut:]

    def _facts_for(
        self, ref: str, source: str, condition: Condition | None
    ) -> _TransitionFacts | None:
        """Read the ``do_…`` function ``ref`` into :class:`_TransitionFacts`."""
        function = self.functions.get(ref)
        if function is None:
            self.bag.emit(
                Codes.AMBIGUOUS_RECONSTRUCTION,
                f"machine '{self.name}' dispatches to '{ref}', which the pack does "
                "not define; that transition is dropped",
                hint="the pack is incomplete — recompiling will not restore it",
                source=self.source,
            )
            return None

        match = _find_comment(function, _TRANSITION_COMMENT)
        if match is None:
            self.bag.emit(
                Codes.AMBIGUOUS_RECONSTRUCTION,
                f"'{ref}' has no '# <source> --<event>--> <target>' comment, so its "
                "event name cannot be recovered",
                hint="the original event name is only stored in that comment",
                source=self.source,
            )
            return None

        commands = _body(function)
        commands = [
            command
            for command in commands
            if _comment_text(command) is None
            or _TRANSITION_COMMENT.match(_comment_text(command) or "") is None
        ]
        for position, command in enumerate(commands):
            if _is_state_write(command, self.name):
                return _TransitionFacts(
                    source=match.group("source"),
                    event=match.group("event"),
                    target=match.group("target"),
                    prefix=commands[:position],
                    enter=commands[position + 1 :],
                    condition=condition,
                )

        self.bag.emit(
            Codes.AMBIGUOUS_RECONSTRUCTION,
            f"'{ref}' never writes the '{STATE_OBJECTIVE}' score, so its target "
            "state cannot be confirmed; the transition is dropped",
            source=self.source,
        )
        return None

    # --- state bodies --------------------------------------------------------
    def _collect_enters(
        self,
        facts: list[_TransitionFacts],
        initial: str,
        initial_enter: list[Command],
    ) -> dict[str, list[Command]]:
        """Each state's enter block, cross-checked across every path into it."""
        candidates: dict[str, list[list[Command]]] = {initial: [initial_enter]}
        for fact in facts:
            candidates.setdefault(fact.target, []).append(fact.enter)

        enters: dict[str, list[Command]] = {}
        for state, options in candidates.items():
            enters[state] = options[0]
            if any(option != options[0] for option in options[1:]):
                self.bag.emit(
                    Codes.AMBIGUOUS_RECONSTRUCTION,
                    f"state '{state}' of machine '{self.name}' is entered with "
                    "different command sequences depending on the path taken; "
                    "using the first",
                    hint="a compiler-generated pack writes the same enter block "
                    "everywhere, so this pack was probably edited by hand",
                    source=self.source,
                )
        return enters

    def _split_exits(self, facts: list[_TransitionFacts]) -> dict[str, list[Command]]:
        """Split each transition's prefix into the source's exit block and its own.

        See the module docstring: the exit block is the longest common prefix of
        every transition leaving that state.
        """
        by_source: dict[str, list[_TransitionFacts]] = {}
        for fact in facts:
            by_source.setdefault(fact.source, []).append(fact)

        exits: dict[str, list[Command]] = {}
        for state, outgoing in by_source.items():
            shared = _common_prefix([fact.prefix for fact in outgoing])
            exits[state] = shared
            for fact in outgoing:
                fact.commands = fact.prefix[len(shared) :]
            if len(outgoing) == 1 and shared:
                self.bag.emit(
                    Codes.AMBIGUOUS_RECONSTRUCTION,
                    f"state '{state}' of machine '{self.name}' has one outgoing "
                    f"transition, so its {len(shared)} leading command(s) could be "
                    "the state's exit block or the transition's own; attributing "
                    "them to the state's exit",
                    hint="both choices recompile to identical output — only the "
                    "naming in the generated Python differs",
                    source=self.source,
                )
        return exits

    def _read_cycles(
        self, index_to_state: dict[int, str], facts: list[_TransitionFacts]
    ) -> dict[str, list[Command]]:
        """Each state's per-tick cycle commands, from its ``tick_<state>`` body."""
        cycles: dict[str, list[Command]] = {}
        for state in index_to_state.values():
            function = self._tick_function(state)
            if function is None:
                continue
            commands = _body(function)
            autos = self._auto_calls(function)
            cycle = commands[: len(commands) - len(autos)]
            if cycle:
                cycles[state] = cycle
        return cycles

    # --- assembly ------------------------------------------------------------
    def _build(
        self,
        index_to_state: dict[int, str],
        initial: str,
        facts: list[_TransitionFacts],
        enters: dict[str, list[Command]],
        exits: dict[str, list[Command]],
        cycles: dict[str, list[Command]],
    ) -> Machine[Any]:
        builder: MachineBuilder[dict[str, Any]] = MachineBuilder({}, name=self.name)
        for index in sorted(index_to_state):
            state = index_to_state[index]
            builder.state(
                state,
                enter=enters.get(state, []),
                exit=exits.get(state, []),
                cycle=cycles.get(state, []),
            )
        for fact in facts:
            builder.transition(
                fact.source,
                fact.event,
                to=fact.target,
                commands=fact.commands,
                condition=fact.condition,
            )
        builder.initial(initial)
        return builder.build()


def machine_names(pack: Datapack) -> list[str]:
    """Every machine the pack appears to define, in declaration order.

    A machine is identified by its ``<ns>:<name>/init`` function — the one file
    lowering always emits for every machine.
    """
    names: list[str] = []
    for function in pack.functions:
        if function.id.namespace != pack.namespace:
            continue
        head, sep, tail = function.id.path.partition("/")
        if sep and tail == "init" and head not in names:
            names.append(head)
    return names


def lift_machines(pack: Datapack, bag: DiagnosticBag) -> list[Machine[Any]]:
    """Reconstruct every machine in ``pack``; an empty list means "not liftable".

    Never raises: a pack that does not follow the grimmcraft conventions (a
    hand-written one) reports ``GD3001`` explaining why level 2 was skipped, and
    the caller falls back to the IR.
    """
    names = machine_names(pack)
    if not names:
        bag.emit(
            Codes.NOT_LIFTABLE,
            "no '<machine>/init' function found, so this pack does not follow the "
            "grimmcraft state-machine convention",
            hint="--emit ir works on any datapack; --emit machine/python needs a "
            "pack produced by grimmcraft-compile",
            source="pack",
        )
        return []

    machines: list[Machine[Any]] = []
    for name in names:
        try:
            machines.append(_MachineLifter(pack, name, bag).lift())
        except NotLiftable as exc:
            bag.emit(
                Codes.NOT_LIFTABLE,
                f"machine '{name}' cannot be reconstructed: {exc}",
                hint="the IR is still available via --emit ir",
                source=f"{pack.namespace}:{name}",
            )
    return machines
