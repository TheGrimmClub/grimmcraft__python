"""Capture — read a box of blocks out of a saved world into a :class:`Structure`.

This is the *saving* half: point it at a world folder and two corners, and it
reads the Anvil region files directly (via ``grimmcraft-world``) to build a
structure you can write out as ``.nbt``. No server, no structure block, no
running game — the world just has to be saved.

Chunks are read once and cached for the duration of a capture, because a box
spanning a few chunks would otherwise re-parse and re-decompress the same chunk
for every column in it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from grimmcraft_core import BlockPos
from grimmcraft_structures.structure import Block, BlockState, Structure
from grimmcraft_world import region

#: Blocks dropped by default: a captured box is mostly air, and vanilla
#: structures omit empty positions so they blend into existing terrain.
DEFAULT_SKIP = ("minecraft:air",)


def _corners(a: BlockPos, b: BlockPos) -> tuple[BlockPos, BlockPos]:
    """The (minimum, maximum) corners of the box spanned by ``a`` and ``b``.

    Either corner may be given first, and in any orientation — the same box
    results, which is what people expect from two clicked positions.
    """
    return (
        BlockPos(min(a.x, b.x), min(a.y, b.y), min(a.z, b.z)),
        BlockPos(max(a.x, b.x), max(a.y, b.y), max(a.z, b.z)),
    )


@dataclass(slots=True)
class WorldBlockReader:
    """Reads individual block states from a saved world, caching chunks.

    Useful on its own for inspecting a world; :func:`capture` is the common case
    built on top of it.
    """

    world_dir: Path
    dimension: str = "overworld"
    _chunks: dict[tuple[int, int], dict[str, Any] | None] = field(
        default_factory=dict, repr=False
    )

    def chunk_for(self, x: int, z: int) -> dict[str, Any] | None:
        """The chunk containing world column ``(x, z)``, read at most once."""
        key = (x >> 4, z >> 4)
        if key not in self._chunks:
            self._chunks[key] = region.read_chunk(
                self.world_dir, key[0], key[1], self.dimension
            )
        return self._chunks[key]

    def state_at(self, pos: BlockPos) -> BlockState | None:
        """The block state at a world position, or ``None`` where none is stored.

        ``None`` means the chunk is ungenerated, predates the 1.18 layout, or the
        position is outside the built height range — not that the block is air.
        """
        chunk = self.chunk_for(pos.x, pos.z)
        if chunk is None:
            return None
        entry = region.chunk_block_state(chunk, pos.x, pos.y, pos.z)
        if entry is None:
            return None
        return BlockState.from_nbt(entry)


def capture(
    world_dir: str | Path,
    corner_a: BlockPos,
    corner_b: BlockPos,
    *,
    dimension: str = "overworld",
    skip: tuple[str, ...] = DEFAULT_SKIP,
    include_air: bool = False,
) -> Structure:
    """Capture the box between two corners of a saved world as a structure.

    The corners are inclusive and may be given in any order. Positions in the
    result are relative to the box's minimum corner, so the structure can be
    placed anywhere.

    ``skip`` names blocks to leave out (air by default, matching vanilla);
    ``include_air=True`` overrides it and captures the box verbatim, which is
    what you want for a sealed room that should replace whatever is there.
    """
    reader = WorldBlockReader(Path(world_dir), dimension)
    low, high = _corners(corner_a, corner_b)
    unwanted: set[str] = (
        set()
        if include_air
        else {name if ":" in name else f"minecraft:{name}" for name in skip}
    )

    blocks: list[Block] = []
    for x in range(low.x, high.x + 1):
        for y in range(low.y, high.y + 1):
            for z in range(low.z, high.z + 1):
                state = reader.state_at(BlockPos(x, y, z))
                if state is None or state.name in unwanted:
                    continue
                blocks.append(
                    Block(
                        pos=BlockPos(x - low.x, y - low.y, z - low.z),
                        state=state,
                    )
                )

    size = (high.x - low.x + 1, high.y - low.y + 1, high.z - low.z + 1)
    return Structure(size=size, blocks=blocks)
