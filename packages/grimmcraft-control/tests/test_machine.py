"""Core state-machine behaviour: dispatch, guards, rejection, builder validation."""

from __future__ import annotations

from typing import Any

import pytest

from grimmcraft_control import (
    Command,
    Event,
    InvalidTransition,
    MachineBuilder,
    MachineBuildError,
)
from grimmcraft_control.demos import door_machine, furnace_machine


def _toggle() -> MachineBuilder[dict[str, Any]]:
    return (
        MachineBuilder[dict[str, Any]]({})
        .named("toggle")
        .state("OFF", enter=(Command("say", {"text": "off"}),))
        .state("ON", enter=(Command("say", {"text": "on"}),))
        .transition("OFF", "flip", to="ON")
        .transition("ON", "flip", to="OFF")
        .initial("OFF")
    )


def test_dispatch_advances_and_emits_commands() -> None:
    m = _toggle().build()
    result = m.dispatch(Event("flip"))
    assert result.ok
    assert result.from_state == "OFF" and result.to_state == "ON"
    assert [c.payload["text"] for c in result.commands] == ["on"]
    assert m.current_state == "ON"


def test_rejected_event_leaves_state_unchanged() -> None:
    m = _toggle().build()
    result = m.dispatch(Event("nonsense"))
    assert not result.ok
    assert result.error is not None
    assert m.current_state == "OFF"


def test_strict_machine_raises_on_no_transition() -> None:
    m = _toggle().build()
    m.strict = True
    with pytest.raises(InvalidTransition):
        m.dispatch(Event("nonsense"))


def test_guard_selects_branch() -> None:
    m = (
        MachineBuilder[dict[str, Any]]({"allowed": False})
        .state("A").state("B")
        .transition("A", "go", to="B", guard=lambda ctx, e: ctx["allowed"])
        .initial("A").build()
    )
    assert not m.dispatch(Event("go")).ok
    m.context["allowed"] = True
    assert m.dispatch(Event("go")).ok


def test_builder_rejects_unknown_state() -> None:
    with pytest.raises(MachineBuildError, match="unknown"):
        (
            MachineBuilder[dict[str, Any]]({})
            .state("A")
            .transition("A", "go", to="MISSING")
            .initial("A").build()
        )


def test_builder_requires_initial() -> None:
    with pytest.raises(MachineBuildError, match="initial"):
        MachineBuilder[dict[str, Any]]({}).state("A").build()


def test_builder_rejects_ambiguous_unguarded() -> None:
    with pytest.raises(MachineBuildError, match="ambiguous"):
        (
            MachineBuilder[dict[str, Any]]({})
            .state("A").state("B").state("C")
            .transition("A", "go", to="B")
            .transition("A", "go", to="C")
            .initial("A").build()
        )


def test_demo_door_lifecycle() -> None:
    door = door_machine()
    assert door.current_state == "CLOSED"
    assert door.dispatch(Event("open")).ok
    assert door.current_state == "OPEN"
    assert door.dispatch(Event("close")).ok
    assert door.dispatch(Event("lock")).ok
    assert door.current_state == "LOCKED"
    assert not door.dispatch(Event("open")).ok  # locked


def test_demo_furnace_has_cycle_and_auto_transition() -> None:
    furnace = furnace_machine()
    smelting = furnace.states["SMELTING"]
    assert smelting.cycle  # per-tick processing loop exists
    autos = [t for t in furnace.transitions_from("SMELTING") if t.event == "tick"]
    assert autos and autos[0].condition is not None
