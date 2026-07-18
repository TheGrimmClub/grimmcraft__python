"""Dialect rendering: components vs NBT, SNBT vs JSON text, positions, states."""

from __future__ import annotations

import pytest

from grimmcraft_compiler.dialect import Dialect, position
from grimmcraft_compiler.target import Target
from grimmcraft_control.machine import Command


def _dialect(version: str) -> Dialect:
    return Dialect(Target.resolve(version, "vanilla"))


@pytest.mark.parametrize(
    "version,expected",
    [
        ("1.20.4", 'give @p minecraft:iron_ingot{display:{Name:\'{"text":"Named"}\'}} 1'),
        ("1.21.1", 'give @p minecraft:iron_ingot[minecraft:custom_name={"text":"Named"}] 1'),
    ],
)
def test_give_components_vs_nbt(version: str, expected: str) -> None:
    cmd = Command("give", {"target": "@p", "item": "minecraft:iron_ingot",
                           "count": 1, "name": "Named"})
    assert _dialect(version).render(cmd) == expected


def test_text_component_json_vs_snbt() -> None:
    assert _dialect("1.21.1").text_component("hi") == '{"text":"hi"}'
    # 1.21.5 switched text components to SNBT (unquoted keys).
    assert _dialect("1.21.5").text_component("hi") == '{text:"hi"}'


def test_setblock_with_state_is_version_stable() -> None:
    cmd = Command("setblock", {"pos": (0, 64, 0), "block": "minecraft:furnace",
                               "state": {"lit": "true"}})
    line = "setblock 0 64 0 minecraft:furnace[lit=true]"
    assert _dialect("1.20.4").render(cmd) == line
    assert _dialect("1.21.1").render(cmd) == line


def test_fill_render_with_and_without_mode() -> None:
    from grimmcraft_control.machine import fill
    from grimmcraft_data import Block

    trunk = fill((0, 64, 0), (0, 68, 0), Block.OAK_LOG)
    assert _dialect("1.21.1").render(trunk) == "fill 0 64 0 0 68 0 minecraft:oak_log"

    leaves = fill((-2, 67, -2), (2, 67, 2), "minecraft:oak_leaves", mode="keep")
    assert _dialect("1.21.1").render(leaves) == (
        "fill -2 67 -2 2 67 2 minecraft:oak_leaves keep"
    )


def test_enum_member_id_is_accepted() -> None:
    from grimmcraft_data import Block

    cmd = Command("setblock", {"pos": (1, 2, 3), "block": Block.STONE})
    assert _dialect("1.21.1").render(cmd) == "setblock 1 2 3 minecraft:stone"


def test_position_formats() -> None:
    assert position((0, 64, 0)) == "0 64 0"
    assert position("~ ~1 ~") == "~ ~1 ~"
    assert position((0.5, 64.0, -1.5)) == "0.5 64 -1.5"


def test_execute_if_score_nesting() -> None:
    inner = Command("call", {"ref": "grimmcraft:door/do_x"})
    cmd = Command("execute_if_score",
                  {"objective": "grimmcraft_state", "entry": "door",
                   "value": 0, "run": inner})
    assert _dialect("1.21.1").render(cmd) == (
        "execute if score door grimmcraft_state matches 0 run "
        "function grimmcraft:door/do_x"
    )


def test_unknown_command_raises() -> None:
    with pytest.raises(ValueError, match="cannot render command"):
        _dialect("1.21.1").render(Command("teleport_all", {}))
