"""The beginner-friendly builder: add_state / add_transition + effect constructors."""

from __future__ import annotations

from typing import Any

from grimmcraft_control import (
    TICK_EVENT,
    CommandName,
    ConditionName,
    Event,
    MachineBuilder,
    add_score,
    new_machine,
    say,
    set_score,
    setblock,
)
from grimmcraft_data import Block


def test_effect_constructors_build_expected_commands() -> None:
    block = setblock((0, 64, 0), Block.LIGHT, level=15)
    assert block.name == CommandName.SETBLOCK
    assert block.payload == {"pos": (0, 64, 0), "block": Block.LIGHT,
                             "state": {"level": "15"}}
    assert say("hi").payload == {"text": "hi"}
    assert set_score("t", "m", 5).name == CommandName.SCOREBOARD_SET
    assert add_score("t", "m", -1).payload["value"] == -1


def test_add_state_and_add_transition_fluent() -> None:
    builder = MachineBuilder[dict[str, Any]]({}).named("lamp")

    off = builder.add_state("OFF")
    off.on_enter(setblock((0, 64, 0), Block.AIR))

    on = builder.add_state("ON")
    on.on_enter(setblock((0, 64, 0), Block.LIGHT, level=15))
    on.on_enter(say("lit"))
    on.on_cycle(add_score("timer", "lamp", -1))

    builder.transition("OFF", "pull", to="ON")
    builder.transition("ON", "pull", to="OFF")
    auto = builder.add_transition("ON", TICK_EVENT, to="OFF")
    auto.when_score("timer", "lamp", 0)

    machine = builder.initial("OFF").build()

    # states carry the commands added one call at a time
    assert [c.name for c in machine.states["ON"].enter] == [
        CommandName.SETBLOCK, CommandName.SAY,
    ]
    assert machine.states["ON"].cycle[0].name == CommandName.SCOREBOARD_ADD

    # the fluent transition is present with its declarative condition
    autos = [t for t in machine.transitions_from("ON") if t.event == TICK_EVENT]
    assert autos and autos[0].condition is not None
    assert autos[0].condition.name == ConditionName.SCORE_MATCHES

    # and it still runs as a normal machine
    assert machine.dispatch(Event("pull")).ok
    assert machine.current_state == "ON"


def test_compact_and_fluent_styles_mix() -> None:
    builder = MachineBuilder[dict[str, Any]]({})
    builder.state("A", enter=(say("hello"),))  # compact
    builder.add_state("B").on_enter(say("world"))  # fluent
    builder.transition("A", "go", to="B")
    machine = builder.initial("A").build()
    assert machine.dispatch(Event("go")).to_state == "B"
    assert machine.states["B"].enter[0].payload == {"text": "world"}


def test_new_machine_and_state_object_references() -> None:
    # new_machine() hides the generic/context ceremony; add_state returns the
    # state object, which transitions/initial accept directly — so a state name
    # is written exactly once and can't drift out of sync.
    builder = new_machine("lamp")
    off = builder.add_state("OFF")
    on = builder.add_state("ON")
    on.on_enter(say("on"))

    builder.transition(off, "pull", to=on)  # pass state objects, not name strings
    builder.initial(off)
    machine = builder.build()

    assert set(machine.states) == {"OFF", "ON"}
    edge = machine.transitions[0]
    assert (edge.source, edge.event, edge.target) == ("OFF", "pull", "ON")
    assert machine.dispatch(Event("pull")).to_state == "ON"


def test_loop_builds_a_checkerboard() -> None:
    # The API is plain Python, so a loop can emit many commands (the chessboard
    # example): an 8x8 board is 64 wool setblocks, half of each colour.
    builder = MachineBuilder[dict[str, Any]]({}).named("board")
    built = builder.add_state("BUILT")
    for row in range(8):
        for col in range(8):
            wool = Block.WHITE_WOOL if (row + col) % 2 == 0 else Block.BLACK_WOOL
            built.on_enter(setblock((col, 64, row), wool))
    builder.add_state("EMPTY")
    builder.transition("EMPTY", "build", to="BUILT")
    machine = builder.initial("EMPTY").build()

    enters = machine.states["BUILT"].enter
    assert len(enters) == 64
    whites = [c for c in enters if c.payload["block"] is Block.WHITE_WOOL]
    assert len(whites) == 32
