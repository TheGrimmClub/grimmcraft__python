"""The library, and the `place` command across control → compiler → decompiler.

`place` is deliberately part of the *shared* vocabulary rather than something
this package renders privately, so these tests check the whole chain: a machine
places a structure, the compiler renders it, and the decompiler reads it back
into the same command.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from grimmcraft_compiler.dialect import Dialect
from grimmcraft_compiler.target import Target
from grimmcraft_control import new_machine
from grimmcraft_control.machine import CommandName
from grimmcraft_core import BlockPos
from grimmcraft_decompiler.diagnostics import DiagnosticBag
from grimmcraft_decompiler.reader import CommandReader
from grimmcraft_structures import Structure, StructureLibrary
from grimmcraft_structures.structure import Block, BlockState


def dialect(version: str = "1.21.11") -> Dialect:
    return Dialect(Target.resolve(version, "vanilla"))


def a_structure() -> Structure:
    return Structure.from_blocks(
        [Block(BlockPos(0, 0, 0), BlockState("minecraft:stone"))]
    )


# --- the library -------------------------------------------------------------
def test_library_ids_are_namespaced() -> None:
    library = StructureLibrary("dungeon")
    assert library.add("room", a_structure()) == "dungeon:room"


def test_library_writes_into_the_datapack_structures_folder(tmp_path: Path) -> None:
    library = StructureLibrary("dungeon")
    library.add("room", a_structure())
    (written,) = library.write_into(tmp_path / "pack")

    assert written == tmp_path / "pack/data/dungeon/structures/room.nbt"
    assert Structure.read(written).blocks[0].state.name == "minecraft:stone"


def test_library_loads_a_directory_of_files(tmp_path: Path) -> None:
    a_structure().write(tmp_path / "a.nbt")
    a_structure().write(tmp_path / "b.nbt")
    library = StructureLibrary("dungeon")

    assert library.load_directory(tmp_path) == ["dungeon:a", "dungeon:b"]
    assert "a" in library and len(library) == 2


# --- rendering ---------------------------------------------------------------
def test_place_renders_as_place_template() -> None:
    builder = new_machine("dungeon")
    with builder.add_state("BUILT") as built:
        built.enter.place("dungeon:room", BlockPos(0, 64, 0))
    machine = builder.initial(built).build()

    (command,) = machine.states["BUILT"].enter
    assert command.name == CommandName.PLACE
    assert dialect().render(command) == "place template dungeon:room 0 64 0"


def test_place_defaults_to_the_current_position() -> None:
    from grimmcraft_control.machine.effects import place

    assert dialect().render(place("dungeon:room")) == "place template dungeon:room ~ ~ ~"


def test_place_renders_rotation_and_mirror() -> None:
    from grimmcraft_control.machine.effects import place

    command = place("dungeon:room", BlockPos(0, 64, 0), rotation="clockwise_90",
                    mirror="front_back")
    assert dialect().render(command) == (
        "place template dungeon:room 0 64 0 clockwise_90 front_back"
    )


def test_mirror_without_rotation_inserts_the_neutral_rotation() -> None:
    """The trailing arguments are positional, so a mirror needs a rotation first."""
    from grimmcraft_control.machine.effects import place

    command = place("dungeon:room", BlockPos(0, 64, 0), mirror="front_back")
    assert dialect().render(command) == (
        "place template dungeon:room 0 64 0 none front_back"
    )


# --- reading it back ---------------------------------------------------------
@pytest.mark.parametrize(
    "line",
    [
        "place template dungeon:room 0 64 0",
        "place template dungeon:room ~ ~ ~",
        "place template dungeon:room 0 64 0 clockwise_90",
        "place template dungeon:room 0 64 0 none front_back",
    ],
)
def test_decompiler_reads_place_back_identically(line: str) -> None:
    """The reader/Dialect symmetry the round-trip guarantee depends on."""
    reader = CommandReader(Target.resolve("1.21.11", "vanilla"), DiagnosticBag())
    command = reader.read(line, source="t")
    assert command.name == CommandName.PLACE
    assert dialect().render(command) == line


@pytest.mark.parametrize(
    "line",
    [
        "place feature minecraft:oak 0 64 0",   # a different `place` sub-command
        "place jigsaw a:b c:d 3 0 64 0",
        "place template dungeon:room 0 64 0 a b c",  # too many arguments
    ],
)
def test_other_place_subcommands_stay_raw(line: str) -> None:
    reader = CommandReader(Target.resolve("1.21.11", "vanilla"), DiagnosticBag())
    command = reader.read(line, source="t")
    assert command.name == CommandName.RAW
    assert dialect().render(command) == line, "nothing is lost"


# --- version gating ----------------------------------------------------------
@pytest.mark.parametrize("version", ["1.20.1", "1.21.11"])
def test_place_is_available_on_every_supported_target(version: str) -> None:
    """`place template` arrived in 1.19, below the oldest version the compiler
    supports (1.20.1) — so the declared ``min_version`` never trips today.

    The declaration is still worth carrying: it is what makes the gate fire on
    its own if an older target is ever added to the support table, and
    :func:`test_the_min_version_gate_would_fire` proves the mechanism works.
    """
    from grimmcraft_compiler.diagnostics import DiagnosticBag as Bag
    from grimmcraft_compiler.validate import validate_machines

    builder = new_machine("dungeon")
    with builder.add_state("BUILT") as built:
        built.enter.place("dungeon:room", BlockPos(0, 64, 0))
    builder.add_state("EMPTY")
    builder.transition(built, "clear", to="EMPTY")
    machine = builder.initial(built).build()

    bag = Bag()
    validate_machines([machine], Target.resolve(version, "vanilla"), bag)
    assert not bag.has_errors


def test_the_min_version_gate_would_fire() -> None:
    """The mechanism `place` relies on, exercised with a version above the target."""
    from grimmcraft_compiler.diagnostics import Codes
    from grimmcraft_compiler.diagnostics import DiagnosticBag as Bag
    from grimmcraft_compiler.validate import validate_machines
    from grimmcraft_control.machine.effects import place

    future = place("dungeon:room", BlockPos(0, 64, 0))
    future = future.with_payload(min_version="1.99")

    builder = new_machine("dungeon")
    with builder.add_state("BUILT") as built:
        built.enter(future)
    builder.add_state("EMPTY")
    builder.transition(built, "clear", to="EMPTY")

    bag = Bag()
    validate_machines(
        [builder.initial(built).build()], Target.resolve("1.21.11", "vanilla"), bag
    )
    assert Codes.UNAVAILABLE_FEATURE in [d.code for d in bag]
