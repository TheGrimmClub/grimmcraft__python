"""The :class:`Structure` value object — Minecraft's ``.nbt`` structure format.

A structure is what a *structure block* saves: a box of blocks, stored as a
**palette** of distinct block states plus one entry per non-empty position
referencing a palette index. That indirection is why a 32×32×32 room of mostly
stone is a few kilobytes rather than a megabyte, and it is the same shape the
game reads, so a file written here can be dropped into
``data/<ns>/structures/`` and placed with ``/place template``.

The on-disk document::

    {
      DataVersion: 4189,
      size: [3, 2, 3],
      palette: [{Name: "minecraft:stone"},
                {Name: "minecraft:oak_log", Properties: {axis: "y"}}],
      blocks: [{state: 0, pos: [0, 0, 0]},
               {state: 1, pos: [1, 1, 2], nbt: {...}}],
      entities: []
    }

Positions are **relative to the structure's own origin**, always non-negative,
which is what makes a structure placeable anywhere.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any

from grimmcraft_core import BlockPos
from grimmcraft_world import nbt

#: The ``DataVersion`` written when the caller does not supply one (1.21.11).
#: Minecraft tolerates an older value — it runs its data fixers — but a *newer*
#: one makes the game refuse the structure outright.
DEFAULT_DATA_VERSION = 4189

#: The block that means "leave whatever is already here" when a structure is
#: placed. Vanilla omits these positions entirely rather than storing air.
VOID_AIR = "minecraft:structure_void"


@dataclass(frozen=True, slots=True)
class BlockState:
    """One entry of a structure's palette: a block id and its properties.

    Properties are strings on both sides of the format (``"true"``, ``"7"``),
    matching how block states are written in commands.
    """

    name: str
    properties: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if ":" not in self.name:
            object.__setattr__(self, "name", f"minecraft:{self.name}")

    @classmethod
    def from_nbt(cls, entry: dict[str, Any]) -> BlockState:
        raw = entry.get("Properties") or {}
        return cls(
            name=str(entry.get("Name", VOID_AIR)),
            properties={str(k): str(v) for k, v in raw.items()},
        )

    def to_nbt(self) -> dict[str, Any]:
        document: dict[str, Any] = {"Name": self.name}
        if self.properties:
            document["Properties"] = dict(self.properties)
        return document

    def __str__(self) -> str:
        """The command form: ``minecraft:oak_log[axis=y]``."""
        if not self.properties:
            return self.name
        props = ",".join(f"{k}={v}" for k, v in sorted(self.properties.items()))
        return f"{self.name}[{props}]"


@dataclass(frozen=True, slots=True)
class Block:
    """One placed block: a position relative to the structure origin, and its state."""

    pos: BlockPos
    state: BlockState
    #: Block-entity data (a chest's contents, a sign's text), if any.
    nbt: dict[str, Any] | None = None


@dataclass(slots=True)
class Structure:
    """A captured box of blocks, readable and writable as a ``.nbt`` file.

    Construct one with :meth:`read`, :func:`~grimmcraft_structures.capture.capture`
    or :meth:`from_blocks`; write it with :meth:`write`.
    """

    size: tuple[int, int, int]
    blocks: list[Block] = field(default_factory=list)
    entities: list[dict[str, Any]] = field(default_factory=list)
    data_version: int = DEFAULT_DATA_VERSION

    # --- construction --------------------------------------------------------
    @classmethod
    def from_blocks(
        cls,
        blocks: list[Block],
        *,
        size: tuple[int, int, int] | None = None,
        data_version: int = DEFAULT_DATA_VERSION,
    ) -> Structure:
        """Build a structure from blocks, sizing it to fit them when not told."""
        if size is None:
            if not blocks:
                size = (0, 0, 0)
            else:
                size = (
                    max(b.pos.x for b in blocks) + 1,
                    max(b.pos.y for b in blocks) + 1,
                    max(b.pos.z for b in blocks) + 1,
                )
        return cls(size=size, blocks=list(blocks), data_version=data_version)

    # --- the NBT document ----------------------------------------------------
    @classmethod
    def from_nbt(cls, document: dict[str, Any]) -> Structure:
        """Read a structure out of a parsed ``.nbt`` document."""
        palette = [
            BlockState.from_nbt(entry) for entry in (document.get("palette") or [])
        ]
        raw_size = list(document.get("size") or [0, 0, 0])
        while len(raw_size) < 3:
            raw_size.append(0)

        blocks: list[Block] = []
        for entry in document.get("blocks") or []:
            index = entry.get("state")
            position = list(entry.get("pos") or [])
            if not isinstance(index, int) or len(position) != 3:
                continue  # a malformed entry is dropped rather than guessed at
            if not 0 <= index < len(palette):
                continue
            blocks.append(
                Block(
                    pos=BlockPos(int(position[0]), int(position[1]), int(position[2])),
                    state=palette[index],
                    nbt=entry.get("nbt"),
                )
            )

        return cls(
            size=(int(raw_size[0]), int(raw_size[1]), int(raw_size[2])),
            blocks=blocks,
            entities=list(document.get("entities") or []),
            data_version=int(document.get("DataVersion", DEFAULT_DATA_VERSION)),
        )

    def to_nbt(self) -> dict[str, Any]:
        """Render this structure as an NBT document ready for :func:`nbt.dump`.

        The palette is rebuilt from the blocks in first-use order, so it never
        carries states that no block references.
        """
        palette: list[BlockState] = []
        index_of: dict[str, int] = {}
        entries: list[dict[str, Any]] = []

        for block in self.blocks:
            key = str(block.state)
            if key not in index_of:
                index_of[key] = len(palette)
                palette.append(block.state)
            entry: dict[str, Any] = {
                "state": index_of[key],
                "pos": [block.pos.x, block.pos.y, block.pos.z],
            }
            if block.nbt:
                entry["nbt"] = block.nbt
            entries.append(entry)

        return {
            "DataVersion": self.data_version,
            "size": list(self.size),
            "palette": [state.to_nbt() for state in palette],
            "blocks": entries,
            "entities": list(self.entities),
        }

    # --- files ---------------------------------------------------------------
    @classmethod
    def read(cls, path: str | Path) -> Structure:
        """Read a ``.nbt`` structure file (as saved by a structure block)."""
        return cls.from_nbt(nbt.load(path))

    def write(self, path: str | Path) -> Path:
        """Write this structure as a gzipped ``.nbt`` file; return the path."""
        return nbt.save(self.to_nbt(), path)

    # --- inspection ----------------------------------------------------------
    @property
    def palette(self) -> list[BlockState]:
        """The distinct block states used, in first-use order."""
        seen: dict[str, BlockState] = {}
        for block in self.blocks:
            seen.setdefault(str(block.state), block.state)
        return list(seen.values())

    @property
    def volume(self) -> int:
        """The bounding box's volume in blocks (including empty positions)."""
        x, y, z = self.size
        return x * y * z

    def block_at(self, pos: BlockPos) -> Block | None:
        """The block at a relative position, or ``None`` if that spot is empty."""
        for block in self.blocks:
            if block.pos == pos:
                return block
        return None

    def __iter__(self) -> Iterator[Block]:
        return iter(self.blocks)

    def __len__(self) -> int:
        return len(self.blocks)

    # --- transformation ------------------------------------------------------
    def offset(self, dx: int = 0, dy: int = 0, dz: int = 0) -> Structure:
        """A copy with every block shifted — useful before merging two structures."""
        return replace(
            self,
            blocks=[
                Block(block.pos.offset(dx, dy, dz), block.state, block.nbt)
                for block in self.blocks
            ],
            size=(self.size[0] + dx, self.size[1] + dy, self.size[2] + dz),
        )

    def without(self, *block_names: str) -> Structure:
        """A copy with the named blocks dropped (typically ``minecraft:air``).

        Vanilla omits empty positions rather than storing air, so dropping air
        after a capture is what makes a structure blend into existing terrain
        instead of carving a box out of it.
        """
        unwanted = {
            name if ":" in name else f"minecraft:{name}" for name in block_names
        }
        return replace(
            self,
            blocks=[b for b in self.blocks if b.state.name not in unwanted],
        )
