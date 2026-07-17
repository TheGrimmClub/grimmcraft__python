"""Lowering: turn a :class:`Machine` into dialect-independent :class:`~.ir` objects.

The mapping is:

* **states → a scoreboard value** — each state gets an integer index; the current
  index lives under the ``grimmcraft_state`` objective keyed by the machine name.
* **events → trigger functions** — ``on_<event>`` dispatches to the transition
  whose source state currently holds.
* **transitions → guarded command sequences** — each becomes a ``do_…`` function
  running ``on_exit`` → the transition's commands → the state write → ``on_enter``.
* **a state's cycle + automatic (``tick``) transitions → the machine's tick
  function** — cycle commands run first, then the auto transitions are checked.

The machine stays the single source of behaviour; this module is a pure backend.
"""

from __future__ import annotations

import re
from typing import Any

from grimmcraft_compiler import commands as cmd
from grimmcraft_compiler.ir import Datapack, Function, FunctionTag, ResourceLocation
from grimmcraft_control.machine import (
    STATE_OBJECTIVE,
    TICK_EVENT,
    Command,
    Machine,
    Transition,
)

_SLUG_RE = re.compile(r"[^a-z0-9_.-]+")


def slug(name: str) -> str:
    """Lowercase ``name`` and replace path-invalid characters with ``_``."""
    return _SLUG_RE.sub("_", name.lower())


def _collect_objectives(machines: list[Machine[Any]]) -> list[str]:
    """Every scoreboard objective referenced anywhere, ``grimmcraft_state`` first."""
    objectives: list[str] = [STATE_OBJECTIVE]

    def scan(command: Command) -> None:
        if command.name in ("scoreboard_set", "scoreboard_add"):
            obj = command.payload.get("objective")
            if isinstance(obj, str) and obj not in objectives:
                objectives.append(obj)

    for machine in machines:
        for state in machine.states.values():
            for group in (state.enter, state.exit, state.cycle):
                for command in group:
                    scan(command)
        for transition in machine.transitions:
            for command in transition.commands:
                scan(command)
    return objectives


def _transition_fn_name(t: Transition) -> str:
    """A stable, path-safe function basename for a transition."""
    return f"do_{slug(t.source)}__{slug(t.event)}__{slug(t.target)}"


class _MachineLowering:
    """Lowers one machine into functions inside a shared :class:`Datapack`."""

    def __init__(self, machine: Machine[Any], pack: Datapack) -> None:
        self.machine = machine
        self.pack = pack
        self.ns = pack.namespace
        self.name = slug(machine.name)
        # Deterministic state -> index mapping in declaration order.
        self.index = {state: i for i, state in enumerate(machine.states)}

    def rl(self, path: str) -> ResourceLocation:
        return ResourceLocation(self.ns, f"{self.name}/{path}")

    def init_id(self) -> ResourceLocation:
        return self.rl("init")

    def tick_id(self) -> ResourceLocation:
        return self.rl("tick")

    def has_tick(self) -> bool:
        """Whether this machine needs a tick function (cycle or auto transitions)."""
        for state in self.machine.states.values():
            if state.cycle:
                return True
        return any(t.event == TICK_EVENT for t in self.machine.transitions)

    def lower(self) -> None:
        self._emit_init()
        self._emit_transitions()
        self._emit_event_dispatchers()
        if self.has_tick():
            self._emit_tick()

    # --- init ----------------------------------------------------------------
    def _emit_init(self) -> None:
        fn = Function(self.init_id(), comment=f"Initialise machine '{self.name}'")
        fn.add(cmd.comment(
            "states: " + ", ".join(f"{s}={i}" for s, i in self.index.items())
        ))
        initial = self.machine.states[self.machine.initial]
        fn.add(cmd.scoreboard_set(STATE_OBJECTIVE, self.name,
                                  self.index[self.machine.initial]))
        for command in initial.enter:
            fn.add(command)
        self.pack.add_function(fn)

    # --- transitions ---------------------------------------------------------
    def _emit_transitions(self) -> None:
        for t in self.machine.transitions:
            fn = Function(
                self.rl(_transition_fn_name(t)),
                comment=f"{t.source} --{t.event}--> {t.target}",
            )
            source = self.machine.states[t.source]
            target = self.machine.states[t.target]
            for command in source.exit:
                fn.add(command)
            for command in t.commands:
                fn.add(command)
            fn.add(cmd.scoreboard_set(STATE_OBJECTIVE, self.name, self.index[t.target]))
            for command in target.enter:
                fn.add(command)
            self.pack.add_function(fn)

    # --- event dispatchers ---------------------------------------------------
    def _emit_event_dispatchers(self) -> None:
        events: dict[str, list[Transition]] = {}
        for t in self.machine.transitions:
            if t.event == TICK_EVENT:
                continue
            events.setdefault(t.event, []).append(t)

        for event, transitions in events.items():
            fn = Function(
                self.rl(f"on_{slug(event)}"),
                comment=f"Handle event '{event}'",
            )
            for t in transitions:
                call = cmd.call(str(self.rl(_transition_fn_name(t))))
                guarded = self._guard_call(t, call)
                fn.add(guarded)
            self.pack.add_function(fn)

    def _guard_call(self, t: Transition, call: Command) -> Command:
        """Wrap ``call`` so it only runs when in ``t.source`` (and its condition)."""
        guarded = cmd.execute_if_score(
            STATE_OBJECTIVE, self.name, self.index[t.source], call
        )
        if t.condition is not None:
            guarded = self._apply_condition(t, guarded)
        return guarded

    def _apply_condition(self, t: Transition, inner: Command) -> Command:
        """Chain a declarative :class:`Condition` in front of ``inner``."""
        cond = t.condition
        assert cond is not None
        if cond.name == "score_matches":
            return cmd.execute_if_score(
                cond.payload["objective"], cond.payload["entry"],
                cond.payload["value"], inner,
            )
        # Unknown condition kinds are reported by the validator; pass through.
        return inner

    # --- tick ----------------------------------------------------------------
    def _emit_tick(self) -> None:
        dispatch = Function(self.tick_id(), comment=f"Per-tick loop for '{self.name}'")
        for state_name, state in self.machine.states.items():
            autos = [
                t for t in self.machine.transitions
                if t.source == state_name and t.event == TICK_EVENT
            ]
            if not state.cycle and not autos:
                continue
            per_state = self.rl(f"tick_{slug(state_name)}")
            dispatch.add(cmd.execute_if_score(
                STATE_OBJECTIVE, self.name, self.index[state_name], cmd.call(str(per_state))
            ))
            body = Function(per_state, comment=f"Tick while in {state_name}")
            for command in state.cycle:
                body.add(command)
            for t in autos:
                call = cmd.call(str(self.rl(_transition_fn_name(t))))
                if t.condition is not None:
                    call = self._apply_condition(t, call)
                body.add(call)
            self.pack.add_function(body)
        self.pack.add_function(dispatch)


def lower(
    machines: list[Machine[Any]], namespace: str, *, description: str
) -> Datapack:
    """Lower ``machines`` into one :class:`Datapack` IR under ``namespace``."""
    pack = Datapack(namespace=namespace, description=description)

    lowerings = [_MachineLowering(m, pack) for m in machines]
    for lowering in lowerings:
        lowering.lower()

    # Global load function: declare objectives, then init every machine.
    load = Function(ResourceLocation(namespace, "load"), comment="Datapack load hook")
    for objective in _collect_objectives(machines):
        load.add(cmd.scoreboard_objective_add(objective))
    for lowering in lowerings:
        load.add(cmd.call(str(lowering.init_id())))
    pack.add_function(load)

    load_tag = FunctionTag(ResourceLocation("minecraft", "load"), [load.id])
    pack.tags.append(load_tag)

    # Global tick function: run every machine that needs a tick loop.
    ticking = [lo for lo in lowerings if lo.has_tick()]
    if ticking:
        tick = Function(ResourceLocation(namespace, "tick"), comment="Datapack tick hook")
        for lowering in ticking:
            tick.add(cmd.call(str(lowering.tick_id())))
        pack.add_function(tick)
        pack.tags.append(
            FunctionTag(ResourceLocation("minecraft", "tick"), [tick.id])
        )

    return pack
