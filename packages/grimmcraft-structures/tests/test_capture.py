"""Capturing a box of blocks out of a saved world's region files."""

from __future__ import annotations

from pathlib import Path

from grimmcraft_core import BlockPos
from grimmcraft_structures import Structure, capture
from grimmcraft_structures.capture import WorldBlockReader


def test_reads_a_block_state_from_the_world(world: Path) -> None:
    reader = WorldBlockReader(world)
    state = reader.state_at(BlockPos(0, 64, 0))
    assert state is not None and state.name == "minecraft:stone"


def test_reads_a_block_with_properties(world: Path) -> None:
    state = WorldBlockReader(world).state_at(BlockPos(1, 65, 2))
    assert state is not None
    assert state.name == "minecraft:oak_log"
    assert state.properties == {"axis": "y"}


def test_ungenerated_chunks_read_as_none(world: Path) -> None:
    """Absent is not the same as air — it must not become a block."""
    assert WorldBlockReader(world).state_at(BlockPos(5000, 64, 5000)) is None


def test_capture_drops_air_by_default(world: Path) -> None:
    structure = capture(world, BlockPos(0, 64, 0), BlockPos(2, 66, 2))
    names = {block.state.name for block in structure}
    assert "minecraft:air" not in names
    assert names == {"minecraft:stone", "minecraft:oak_log"}


def test_capture_keeps_air_when_asked(world: Path) -> None:
    structure = capture(
        world, BlockPos(0, 64, 0), BlockPos(2, 66, 2), include_air=True
    )
    assert "minecraft:air" in {block.state.name for block in structure}


def test_capture_positions_are_relative_to_the_minimum_corner(world: Path) -> None:
    """A structure must be placeable anywhere, so it stores its own origin."""
    structure = capture(world, BlockPos(1, 64, 1), BlockPos(3, 66, 3))
    assert all(b.pos.x >= 0 and b.pos.y >= 0 and b.pos.z >= 0 for b in structure)
    assert structure.block_at(BlockPos(0, 0, 0)) is not None  # world (1,64,1)


def test_corners_may_be_given_in_any_order(world: Path) -> None:
    forward = capture(world, BlockPos(0, 64, 0), BlockPos(2, 66, 2))
    backward = capture(world, BlockPos(2, 66, 2), BlockPos(0, 64, 0))
    assert forward.size == backward.size
    assert len(forward) == len(backward)


def test_capture_size_is_the_inclusive_box(world: Path) -> None:
    structure = capture(world, BlockPos(0, 64, 0), BlockPos(2, 65, 3))
    assert structure.size == (3, 2, 4)


def test_captured_structure_round_trips_to_a_file(world: Path, tmp_path: Path) -> None:
    """The end-to-end promise: world → Structure → .nbt → Structure."""
    captured = capture(world, BlockPos(0, 64, 0), BlockPos(3, 65, 3))
    restored = Structure.read(captured.write(tmp_path / "room.nbt"))

    assert restored.size == captured.size
    assert len(restored) == len(captured)
    assert {str(b.state) for b in restored} == {str(b.state) for b in captured}


def test_capture_of_empty_space_yields_no_blocks(world: Path) -> None:
    structure = capture(world, BlockPos(0, 70, 0), BlockPos(2, 72, 2))
    assert len(structure) == 0
    assert structure.size == (3, 3, 3), "the box is still recorded"
