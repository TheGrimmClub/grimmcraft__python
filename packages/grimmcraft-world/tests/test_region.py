"""Tests for grimmcraft_world.region, using a hand-built Anvil region file."""

from __future__ import annotations

import struct
import zlib
from pathlib import Path

from grimmcraft_world import nbt, region

# --- tiny NBT + Anvil encoders (just enough to build a fixture) -------------

def _str(text: str) -> bytes:
    return struct.pack(">H", len(text)) + text.encode()


def _int(name: str, value: int) -> bytes:
    return bytes([nbt.TAG_INT]) + _str(name) + struct.pack(">i", value)


def _string(name: str, value: str) -> bytes:
    return bytes([nbt.TAG_STRING]) + _str(name) + _str(value)


def _compound_body(*members: bytes) -> bytes:
    return b"".join(members) + bytes([nbt.TAG_END])


def _block_entity(block_id: str, x: int, y: int, z: int, command: str = "") -> bytes:
    return _compound_body(
        _string("id", block_id), _int("x", x), _int("y", y), _int("z", z),
        _string("Command", command),
    )


def _chunk_nbt(block_entities: list[bytes]) -> bytes:
    # TAG_List of TAG_Compound
    list_payload = bytes([nbt.TAG_COMPOUND]) + struct.pack(">i", len(block_entities))
    list_payload += b"".join(block_entities)
    body = bytes([nbt.TAG_LIST]) + _str("block_entities") + list_payload + bytes([nbt.TAG_END])
    return bytes([nbt.TAG_COMPOUND]) + struct.pack(">H", 0) + body  # unnamed root


def _region_bytes(chunk_nbt: bytes) -> bytes:
    compressed = zlib.compress(chunk_nbt)
    payload = struct.pack(">i", len(compressed) + 1) + bytes([2]) + compressed  # 2 = zlib
    sectors = (len(payload) + region.SECTOR - 1) // region.SECTOR
    chunk_sector = payload + b"\x00" * (sectors * region.SECTOR - len(payload))
    header = bytearray(2 * region.SECTOR)  # locations + timestamps
    header[0:3] = (2).to_bytes(3, "big")   # chunk 0 starts at sector 2
    header[3] = sectors
    return bytes(header) + chunk_sector


def _make_region(path: Path, block_entities: list[bytes]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(_region_bytes(_chunk_nbt(block_entities)))


# --- tests ------------------------------------------------------------------

def test_iter_region_chunks_roundtrip(tmp_path: Path):
    mca = tmp_path / "r.0.0.mca"
    _make_region(mca, [_block_entity("minecraft:command_block", 1, 2, 3, "say hi")])
    chunks = list(region.iter_region_chunks(mca))
    assert len(chunks) == 1
    entities = region.chunk_block_entities(chunks[0])
    assert entities[0]["id"] == "minecraft:command_block"
    assert entities[0]["Command"] == "say hi"


def test_iter_block_entities_overworld(tmp_path: Path):
    world = tmp_path / "world"
    _make_region(
        world / "region" / "r.0.0.mca",
        [
            _block_entity("minecraft:command_block", 10, 64, -5, "tp @p 0 0 0"),
            _block_entity("minecraft:chest", 1, 2, 3),
        ],
    )
    found = list(region.iter_block_entities(world))
    assert len(found) == 2
    assert {dim for dim, _ in found} == {"overworld"}


def test_dimension_names(tmp_path: Path):
    world = tmp_path / "world"
    _make_region(world / "DIM1" / "region" / "r.0.0.mca",
                 [_block_entity("minecraft:command_block", 0, 0, 0, "time set day")])
    dims = {dim for dim, _ in region.iter_block_entities(world)}
    assert dims == {"the_end"}


def test_empty_region_is_skipped(tmp_path: Path):
    mca = tmp_path / "region" / "r.0.0.mca"
    mca.parent.mkdir(parents=True)
    mca.write_bytes(b"\x00" * region.SECTOR)  # header only, no chunks
    assert list(region.iter_region_chunks(mca)) == []
