"""Fixtures: a real ``.mca`` region file, built from scratch.

Capture reads Anvil region files, so testing it hermetically means *writing* one.
That is only possible because the NBT writer exists — which makes these tests a
genuine end-to-end exercise of both halves of the format.
"""

from __future__ import annotations

import zlib
from pathlib import Path

import pytest

from grimmcraft_world import nbt
from grimmcraft_world.region import SECTOR

#: A 16x16x16 section's worth of block indices.
_SECTION_CELLS = 4096


def build_chunk(
    chunk_x: int, chunk_z: int, palette: list[dict[str, object]], indices: list[int]
) -> dict[str, object]:
    """A 1.18+ chunk whose section Y=4 (world y 64..79) holds ``indices``.

    ``indices`` are palette positions in Minecraft's YZX order, bit-packed the
    1.16+ way: entries never straddle two longs.
    """
    bits = max(4, (len(palette) - 1).bit_length())
    per_long = 64 // bits
    longs: list[int] = []
    for start in range(0, _SECTION_CELLS, per_long):
        packed = 0
        for slot, index in enumerate(indices[start : start + per_long]):
            packed |= (index & ((1 << bits) - 1)) << (slot * bits)
        # NBT longs are signed; wrap the high bit like Java would.
        longs.append(packed - (1 << 64) if packed >= (1 << 63) else packed)

    return {
        "DataVersion": 4189,
        "xPos": chunk_x,
        "zPos": chunk_z,
        "sections": [
            {
                "Y": 4,
                "block_states": {
                    "palette": palette,
                    "data": nbt.LongArray(longs),
                },
            }
        ],
        "block_entities": [],
    }


def write_region(path: Path, chunks: dict[tuple[int, int], dict[str, object]]) -> Path:
    """Write ``chunks`` into an ``r.0.0.mca`` region file at ``path``."""
    header = bytearray(SECTOR * 2)  # location table + timestamp table
    body = bytearray()
    sector = 2  # data starts after the two header sectors

    for (chunk_x, chunk_z), chunk in chunks.items():
        payload = zlib.compress(nbt.dump(chunk, gzipped=False))
        block = bytearray()
        block += (len(payload) + 1).to_bytes(4, "big")
        block += b"\x02"  # compression scheme 2 = zlib
        block += payload
        # each chunk is padded out to a whole number of 4 KiB sectors
        used = (len(block) + SECTOR - 1) // SECTOR
        block += b"\x00" * (used * SECTOR - len(block))

        index = (chunk_x & 31) + (chunk_z & 31) * 32
        header[index * 4 : index * 4 + 3] = sector.to_bytes(3, "big")
        header[index * 4 + 3] = used
        body += block
        sector += used

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(bytes(header) + bytes(body))
    return path


@pytest.fixture
def world(tmp_path: Path) -> Path:
    """A world whose chunk (0,0) is stone at y=64, with one oak log at (1,65,2).

    Everything else in the section is air, so a capture must drop it by default.
    """
    palette: list[dict[str, object]] = [
        {"Name": "minecraft:air"},
        {"Name": "minecraft:stone"},
        {"Name": "minecraft:oak_log", "Properties": {"axis": "y"}},
    ]
    indices = [0] * _SECTION_CELLS

    def cell(x: int, y: int, z: int) -> int:
        return (y & 15) * 256 + (z & 15) * 16 + (x & 15)

    for x in range(16):
        for z in range(16):
            indices[cell(x, 64, z)] = 1  # a floor of stone at y=64
    indices[cell(1, 65, 2)] = 2  # one oak log standing on it

    root = tmp_path / "world"
    write_region(root / "region" / "r.0.0.mca", {(0, 0): build_chunk(0, 0, palette, indices)})
    (root / "level.dat").write_bytes(nbt.dump({"Data": {"LevelName": "test"}}))
    return root
