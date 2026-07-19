"""Machine reconstruction: does the lifter recover what lowering encoded?

Every assertion here compares against the *original* machine the fixture was
compiled from, so these tests check semantic recovery rather than merely that
some machine came back.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from grimmcraft_control.demos import door_machine, furnace_machine
from grimmcraft_control.machine import TICK_EVENT, Machine
from grimmcraft_decompiler import decompile
from grimmcraft_decompiler.diagnostics import Codes

from .conftest import VERSIONS, build_pack


def lift(path: Path) -> list[Machine[Any]]:
    result = decompile(path, emit="machine")
    return result.machines


@pytest.mark.parametrize("version", VERSIONS)
def test_states_and_initial_are_recovered(tmp_path: Path, version: str) -> None:
    original = door_machine()
    pack = build_pack([original], tmp_path / "p", version)
    (rebuilt,) = lift(pack)

    assert rebuilt.name == original.name
    assert list(rebuilt.states) == list(original.states)
    assert rebuilt.initial == original.initial


@pytest.mark.parametrize("version", VERSIONS)
def test_transitions_are_recovered(tmp_path: Path, version: str) -> None:
    original = door_machine()
    pack = build_pack([original], tmp_path / "p", version)
    (rebuilt,) = lift(pack)

    def edges(machine: Machine[Any]) -> set[tuple[str, str, str]]:
        return {(t.source, t.event, t.target) for t in machine.transitions}

    assert edges(rebuilt) == edges(original)


@pytest.mark.parametrize("version", VERSIONS)
def test_state_names_keep_their_original_casing(tmp_path: Path, version: str) -> None:
    """Paths are slugged to lowercase; the '# states:' comment carries the real names."""
    pack = build_pack([door_machine()], tmp_path / "p", version)
    (rebuilt,) = lift(pack)
    assert "CLOSED" in rebuilt.states
    assert "closed" not in rebuilt.states


def test_enter_commands_are_recovered(tmp_path: Path) -> None:
    """Enter blocks come back equivalent — compared as rendered commands.

    Not as *identical payloads*: an author may write ``Block.REDSTONE_LAMP``
    where the pack only records ``minecraft:redstone_lamp``. The enum member is
    unrecoverable from text and irrelevant to behaviour, so rendered equality is
    the honest bar.
    """
    from grimmcraft_compiler.dialect import Dialect
    from grimmcraft_compiler.target import Target

    original = door_machine()
    pack = build_pack([original], tmp_path / "p", "1.21.11")
    (rebuilt,) = lift(pack)
    dialect = Dialect(Target.resolve("1.21.11", "vanilla"))

    for name, state in original.states.items():
        assert [dialect.render(c) for c in rebuilt.states[name].enter] == [
            dialect.render(c) for c in state.enter
        ], name


def test_cycle_and_tick_transition_are_separated(tmp_path: Path) -> None:
    """A tick body is cycle effects followed by auto transitions — split correctly."""
    original = furnace_machine()
    pack = build_pack([original], tmp_path / "p", "1.21.11")
    (rebuilt,) = lift(pack)

    smelting = rebuilt.states["SMELTING"]
    assert list(smelting.cycle) == list(original.states["SMELTING"].cycle)

    autos = [t for t in rebuilt.transitions if t.event == TICK_EVENT]
    assert len(autos) == 1
    assert autos[0].source == "SMELTING"


def test_tick_transition_condition_is_recovered(tmp_path: Path) -> None:
    pack = build_pack([furnace_machine()], tmp_path / "p", "1.21.11")
    (rebuilt,) = lift(pack)

    (auto,) = [t for t in rebuilt.transitions if t.event == TICK_EVENT]
    assert auto.condition is not None
    assert auto.condition.payload["objective"] == "furnace_timer"
    assert auto.condition.payload["value"] == 0


def test_several_machines_are_lifted_independently(tmp_path: Path) -> None:
    pack = build_pack(
        [door_machine(), furnace_machine()], tmp_path / "p", "1.21.11"
    )
    machines = lift(pack)
    assert sorted(m.name for m in machines) == ["door", "furnace"]


def test_single_outgoing_transition_reports_the_ambiguity(tmp_path: Path) -> None:
    """The exit/commands split is undecidable with one outgoing edge — say so."""
    pack = build_pack([furnace_machine()], tmp_path / "p", "1.21.11")
    result = decompile(pack, emit="machine")
    assert Codes.AMBIGUOUS_RECONSTRUCTION in [d.code for d in result.diagnostics]


def test_handwritten_pack_is_not_liftable_but_still_yields_ir(
    handwritten_pack: Path,
) -> None:
    result = decompile(handwritten_pack, emit="python")
    assert result.machines == []
    assert Codes.NOT_LIFTABLE in [d.code for d in result.diagnostics]
    assert result.pack.functions, "the IR is still produced"
    assert "function custom:start" in result.output, "falls back to the IR dump"


def test_lifting_survives_a_missing_states_comment(tmp_path: Path) -> None:
    """Without the '# states:' comment the names are gone — report, do not crash."""
    pack = build_pack([door_machine()], tmp_path / "p", "1.21.11")
    init = pack / "data" / "test" / "function" / "door" / "init.mcfunction"
    init.write_text(
        "\n".join(
            line
            for line in init.read_text(encoding="utf-8").splitlines()
            if not line.startswith("# states:")
        )
        + "\n",
        encoding="utf-8",
    )
    result = decompile(pack, emit="machine")
    assert result.machines == []
    assert Codes.NOT_LIFTABLE in [d.code for d in result.diagnostics]
