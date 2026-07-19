"""The Structure value object and its .nbt round-trip."""

from __future__ import annotations

from pathlib import Path

from grimmcraft_core import BlockPos
from grimmcraft_structures import Block, BlockState, Structure
from grimmcraft_world import nbt


def sample() -> Structure:
    return Structure.from_blocks(
        [
            Block(BlockPos(0, 0, 0), BlockState("minecraft:stone")),
            Block(BlockPos(1, 0, 0), BlockState("minecraft:stone")),
            Block(
                BlockPos(1, 1, 0),
                BlockState("minecraft:oak_log", {"axis": "y"}),
                nbt={"custom": "data"},
            ),
        ]
    )


def test_block_state_renders_like_a_command() -> None:
    assert str(BlockState("minecraft:stone")) == "minecraft:stone"
    assert (
        str(BlockState("minecraft:oak_log", {"axis": "y"}))
        == "minecraft:oak_log[axis=y]"
    )


def test_bare_block_names_get_the_minecraft_namespace() -> None:
    assert BlockState("stone").name == "minecraft:stone"


def test_palette_deduplicates_in_first_use_order() -> None:
    structure = sample()
    assert [state.name for state in structure.palette] == [
        "minecraft:stone",
        "minecraft:oak_log",
    ]


def test_size_is_inferred_from_the_blocks() -> None:
    assert sample().size == (2, 2, 1)


def test_nbt_document_uses_palette_indices() -> None:
    document = sample().to_nbt()
    assert len(document["palette"]) == 2
    assert [entry["state"] for entry in document["blocks"]] == [0, 0, 1]
    assert document["blocks"][2]["pos"] == [1, 1, 0]
    assert document["blocks"][2]["nbt"] == {"custom": "data"}


def test_file_roundtrip(tmp_path: Path) -> None:
    """Write a structure, read it back, and get the same blocks."""
    original = sample()
    path = original.write(tmp_path / "s.nbt")
    restored = Structure.read(path)

    assert restored.size == original.size
    assert len(restored) == len(original)
    for before, after in zip(original, restored, strict=True):
        assert after.pos == before.pos
        assert str(after.state) == str(before.state)
        assert after.nbt == before.nbt


def test_written_file_is_gzipped_nbt(tmp_path: Path) -> None:
    """Minecraft expects a gzipped NBT document — not raw, not JSON."""
    path = sample().write(tmp_path / "s.nbt")
    assert path.read_bytes()[:2] == b"\x1f\x8b"
    assert "palette" in nbt.load(path)


def test_block_at_finds_and_misses() -> None:
    structure = sample()
    found = structure.block_at(BlockPos(1, 1, 0))
    assert found is not None and found.state.name == "minecraft:oak_log"
    assert structure.block_at(BlockPos(9, 9, 9)) is None


def test_without_drops_named_blocks() -> None:
    trimmed = sample().without("minecraft:stone")
    assert len(trimmed) == 1
    assert trimmed.blocks[0].state.name == "minecraft:oak_log"


def test_without_accepts_bare_names() -> None:
    assert len(sample().without("stone")) == 1


def test_offset_shifts_every_block() -> None:
    moved = sample().offset(dy=10)
    assert [b.pos.y for b in moved] == [10, 10, 11]


def test_empty_structure_is_valid(tmp_path: Path) -> None:
    empty = Structure.from_blocks([])
    assert empty.size == (0, 0, 0)
    restored = Structure.read(empty.write(tmp_path / "e.nbt"))
    assert len(restored) == 0


def test_malformed_entries_are_dropped_not_guessed() -> None:
    """A hand-edited file should degrade, not crash or invent blocks."""
    structure = Structure.from_nbt(
        {
            "size": [1, 1, 1],
            "palette": [{"Name": "minecraft:stone"}],
            "blocks": [
                {"state": 0, "pos": [0, 0, 0]},
                {"state": 7, "pos": [0, 0, 1]},   # index outside the palette
                {"state": 0, "pos": [0, 0]},      # not three coordinates
                {"pos": [0, 1, 0]},               # no state at all
            ],
        }
    )
    assert len(structure) == 1
