"""The reader is the Dialect run backwards — these tests pin that symmetry.

The central property is ``render(read(line)) == line``.  Most cases below assert
it directly, because a reader that satisfies it for every line the compiler can
emit is exactly what makes the round-trip guarantee hold.
"""

from __future__ import annotations

import pytest

from grimmcraft_compiler.dialect import Dialect
from grimmcraft_compiler.target import Target
from grimmcraft_control.machine import CommandName
from grimmcraft_core import BlockPos
from grimmcraft_decompiler.diagnostics import Codes, DiagnosticBag
from grimmcraft_decompiler.reader import CommandReader

#: Lines every supported version renders identically.
COMMON_LINES = [
    "say The lamp glows.",
    "setblock 0 64 0 minecraft:air",
    "setblock 0 64 0 minecraft:light[level=15]",
    "fill -2 64 -2 2 71 2 minecraft:air",
    "fill 0 64 0 0 69 0 minecraft:spruce_log keep",
    "summon minecraft:pig 3 64 0",
    "particle minecraft:flame 3 64 0",
    "playsound minecraft:block.lever.click master @a",
    "function tutorial:lamp/init",
    "scoreboard objectives add grimmcraft_state dummy",
    "scoreboard players set lamp grimmcraft_state 1",
    "scoreboard players add lamp lamp_timer -1",
    "execute if score lamp grimmcraft_state matches 1 run function tutorial:lamp/tick_on",
    "execute if score spruce spruce_stage matches 2 run fill -2 66 -2 2 66 2 "
    "minecraft:spruce_leaves keep",
    "# a comment",
]


def reader(version: str) -> tuple[CommandReader, DiagnosticBag]:
    bag = DiagnosticBag()
    return CommandReader(Target.resolve(version, "vanilla"), bag), bag


@pytest.mark.parametrize("version", ["1.20.4", "1.21.1", "1.21.11"])
@pytest.mark.parametrize("line", COMMON_LINES)
def test_render_read_is_identity(version: str, line: str) -> None:
    read, _ = reader(version)
    dialect = Dialect(Target.resolve(version, "vanilla"))
    assert dialect.render(read.read(line, source="t")) == line


def test_nbt_item_data_before_1_20_5() -> None:
    """Before 1.20.5 a custom item name is NBT — and must read back as one."""
    line = (
        "give @p minecraft:iron_ingot{display:{Name:'{\"text\":\"Shiny\"}'}} 1"
    )
    read, bag = reader("1.20.4")
    command = read.read(line, source="t")
    assert command.name == CommandName.GIVE
    assert command.payload["name"] == "Shiny"
    assert command.payload["item"] == "minecraft:iron_ingot"
    assert Dialect(Target.resolve("1.20.4", "vanilla")).render(command) == line
    assert not list(bag)


def test_component_item_data_from_1_20_5() -> None:
    """From 1.20.5 the same name is a component; 1.21.5+ writes it as SNBT."""
    line = (
        "give @p minecraft:iron_ingot"
        '[minecraft:custom_name={text:"Freshly Smelted Ingot"}] 1'
    )
    read, bag = reader("1.21.11")
    command = read.read(line, source="t")
    assert command.payload["name"] == "Freshly Smelted Ingot"
    assert Dialect(Target.resolve("1.21.11", "vanilla")).render(command) == line
    assert not list(bag)


def test_json_text_component_before_1_21_5() -> None:
    line = 'tellraw @a {"text":"hello"}'
    read, _ = reader("1.21.4")
    command = read.read(line, source="t")
    assert command.payload["text"] == "hello"
    assert Dialect(Target.resolve("1.21.4", "vanilla")).render(command) == line


def test_snbt_text_component_from_1_21_5() -> None:
    line = 'tellraw @a {text:"hello"}'
    read, _ = reader("1.21.5")
    command = read.read(line, source="t")
    assert command.payload["text"] == "hello"
    assert Dialect(Target.resolve("1.21.5", "vanilla")).render(command) == line


def test_data_model_mismatch_is_reported() -> None:
    """NBT item data on a components-era target means the pack disagrees with itself."""
    read, bag = reader("1.21.11")
    read.read(
        "give @p minecraft:iron_ingot{display:{Name:'{\"text\":\"Shiny\"}'}} 1",
        source="t",
    )
    assert [d.code for d in bag] == [Codes.DATA_MODEL_MISMATCH]


def test_integer_positions_become_blockpos() -> None:
    read, _ = reader("1.21.11")
    command = read.read("setblock 1 -64 3 minecraft:stone", source="t")
    assert command.payload["pos"] == BlockPos(1, -64, 3)


@pytest.mark.parametrize(
    "line",
    [
        "setblock ~ ~1 ~ minecraft:stone",          # relative
        "setblock ^ ^ ^2 minecraft:stone",          # local
        "setblock 0.5 64.0 0.5 minecraft:stone",    # decimal
        "setblock 07 64 0 minecraft:stone",         # non-canonical integer
    ],
)
def test_non_integer_positions_stay_text(line: str) -> None:
    """Anything an int cannot represent exactly is kept verbatim, not normalised."""
    read, _ = reader("1.21.11")
    command = read.read(line, source="t")
    assert isinstance(command.payload["pos"], str)
    assert Dialect(Target.resolve("1.21.11", "vanilla")).render(command) == line


@pytest.mark.parametrize(
    "line",
    [
        "### banner ###",                                   # not "# " prefixed
        "#tight comment",
        'tellraw @a ["",{"text":"hi","color":"green"}]',    # rich component
        "summon firework_rocket ~ ~1 ~ {LifeTime:45}",      # NBT payload
        "scoreboard objectives setdisplay sidebar Feuerwerk",
        "execute as @e[tag=x] at @s run kill @s",
        "scoreboard players set timer custom 1 ",           # trailing space
        "execute if score a b matches 1..5 run say ranged",  # range, not an int
    ],
)
def test_unmodellable_lines_survive_as_raw(line: str) -> None:
    """Nothing is lost: what cannot be modelled re-renders byte for byte."""
    read, _ = reader("1.21.11")
    command = read.read(line, source="t")
    assert command.name == CommandName.RAW
    assert Dialect(Target.resolve("1.21.11", "vanilla")).render(command) == line


def test_blank_line_is_preserved() -> None:
    read, bag = reader("1.21.11")
    command = read.read("", source="t")
    assert Dialect(Target.resolve("1.21.11", "vanilla")).render(command) == ""
    assert not list(bag), "a blank line is not a parse failure"


def test_unparseable_command_is_diagnosed_once() -> None:
    read, bag = reader("1.21.11")
    read.read("execute as @e[tag=x] at @s run kill @s", source="fn.mcfunction:3")
    codes = [d.code for d in bag]
    assert codes == [Codes.UNPARSEABLE_COMMAND]
    assert list(bag)[0].source == "fn.mcfunction:3"


def test_nested_execute_with_opaque_body_stays_whole() -> None:
    """A structured guard around an unmodellable body would trap the lifter."""
    line = "execute if score a b matches 1 run kill @e[tag=x]"
    read, _ = reader("1.21.11")
    command = read.read(line, source="t")
    assert command.name == CommandName.RAW
