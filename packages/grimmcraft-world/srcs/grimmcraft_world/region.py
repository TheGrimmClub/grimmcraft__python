"""Read Minecraft's Anvil region files (``r.X.Z.mca``).

A region file packs 32×32 chunks. Its layout:

- 4096-byte *location* table: 1024 entries of ``offset(3 bytes) + sectors(1)``
- 4096-byte *timestamp* table (we ignore it)
- then each chunk at ``offset * 4096``: ``length(4 bytes) + compression(1) + data``

The chunk ``data`` is compressed NBT; :func:`grimmcraft_world.nbt.parse` auto-detects
the gzip/zlib compression, so we just hand it the payload. This module is the
low-level reader; higher-level tools (scout, blacksmith) build on it.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import Any

from grimmclub_filesystem.paths import as_path
from grimmcraft_world import nbt

SECTOR = 4096

# Region sub-folders per dimension, mapped to friendly names.
DIMENSION_DIRS = {
    "region": "overworld",
    "DIM-1/region": "the_nether",
    "DIM1/region": "the_end",
}


def _chunk_payload(data: bytes, index: int) -> bytes | None:
    """Return the compressed NBT bytes for chunk ``index`` (0..1023), or None."""
    entry = data[index * 4 : index * 4 + 4]
    if len(entry) < 4:
        return None
    offset = int.from_bytes(entry[:3], "big")
    sectors = entry[3]
    if offset == 0 or sectors == 0:
        return None  # chunk not generated
    start = offset * SECTOR
    if start + 5 > len(data):
        return None
    length = int.from_bytes(data[start : start + 4], "big")
    if length <= 1:
        return None
    # length counts the 1 compression-type byte plus the compressed data
    return data[start + 5 : start + 4 + length]


def iter_region_chunks(region_path: str | Path) -> Iterator[dict[str, Any]]:
    """Yield the parsed NBT of every generated chunk in one ``.mca`` file."""
    data = as_path(region_path).read_bytes()
    if len(data) < SECTOR:
        return
    for index in range(1024):
        payload = _chunk_payload(data, index)
        if payload is None:
            continue
        try:
            yield nbt.parse(payload)
        except (ValueError, EOFError, OSError):
            continue  # skip a corrupt chunk rather than fail the whole scan


def chunk_block_entities(chunk: dict[str, Any]) -> list[dict[str, Any]]:
    """Return a chunk's block entities (handles 1.18+ and older layouts)."""
    if "block_entities" in chunk:
        return chunk.get("block_entities") or []
    level = chunk.get("Level") or {}
    return level.get("TileEntities") or []


def chunk_block_state(
    chunk: dict[str, Any], x: int, y: int, z: int
) -> dict[str, Any] | None:
    """Return the block-state palette entry at absolute world coords.

    The result looks like ``{"Name": "minecraft:chain_command_block",
    "Properties": {"conditional": "true", "facing": "east"}}`` — Properties
    may be absent. Only the 1.18+ chunk layout (``sections``) is supported;
    older chunks return None.

    Block states live in 16x16x16 *sections*: each section has a ``palette``
    of distinct states and a ``data`` long-array of bit-packed palette
    indices (1.16+ packing: indices never span two longs).
    """
    for section in chunk.get("sections") or []:
        if section.get("Y") != y >> 4:
            continue
        states = section.get("block_states") or {}
        palette = states.get("palette") or []
        if not palette:
            return None
        data = states.get("data")
        if len(palette) == 1 or not data:
            # the whole section is a single block state
            first: dict[str, Any] = palette[0]
            return first
        bits = max(4, (len(palette) - 1).bit_length())
        per_long = 64 // bits
        index = (y & 15) * 256 + (z & 15) * 16 + (x & 15)
        if index // per_long >= len(data):
            return None
        packed = data[index // per_long] & 0xFFFFFFFFFFFFFFFF  # signed long -> unsigned
        entry = (packed >> ((index % per_long) * bits)) & ((1 << bits) - 1)
        return palette[entry] if entry < len(palette) else None
    return None


def region_file(world_dir: str | Path, chunk_x: int, chunk_z: int,
                dimension: str = "overworld") -> Path:
    """The ``r.X.Z.mca`` path holding chunk ``(chunk_x, chunk_z)``.

    A region file covers 32×32 chunks, so the region coordinates are the chunk
    coordinates shifted right by 5.
    """
    folder = next(
        (rel for rel, name in DIMENSION_DIRS.items() if name == dimension), "region"
    )
    return as_path(world_dir) / folder / f"r.{chunk_x >> 5}.{chunk_z >> 5}.mca"


def read_chunk(
    world_dir: str | Path, chunk_x: int, chunk_z: int,
    dimension: str = "overworld",
) -> dict[str, Any] | None:
    """The parsed NBT of one chunk, or ``None`` if it is absent or ungenerated.

    Reads only the requested chunk out of its region file, rather than scanning
    the whole file like :func:`iter_region_chunks`.
    """
    path = region_file(world_dir, chunk_x, chunk_z, dimension)
    if not path.is_file():
        return None
    data = path.read_bytes()
    if len(data) < SECTOR:
        return None
    index = (chunk_x & 31) + (chunk_z & 31) * 32
    payload = _chunk_payload(data, index)
    if payload is None:
        return None
    try:
        return nbt.parse(payload)
    except (ValueError, EOFError, OSError):
        return None


def iter_region_files(world_dir: str | Path) -> Iterator[tuple[str, Path]]:
    """Yield ``(dimension_name, path)`` for every region file in a world."""
    world = as_path(world_dir)
    for rel, dimension in DIMENSION_DIRS.items():
        folder = world / rel
        if folder.is_dir():
            for mca in sorted(folder.glob("*.mca")):
                yield dimension, mca


def iter_block_entities(
    world_dir: str | Path,
) -> Iterator[tuple[str, dict[str, Any]]]:
    """Yield ``(dimension_name, block_entity)`` for the whole world."""
    for dimension, path in iter_region_files(world_dir):
        for chunk in iter_region_chunks(path):
            for entity in chunk_block_entities(chunk):
                yield dimension, entity
