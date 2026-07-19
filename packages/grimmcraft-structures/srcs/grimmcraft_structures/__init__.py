"""grimmcraft-structures — save and restore Minecraft structures.

Three things, matching how structures are actually used to build a map out of
predefined pieces:

1. **Save** — :func:`capture` reads a box of blocks straight out of a saved
   world's region files into a :class:`Structure`. No server, no structure
   block; the world just has to be saved.
2. **Store** — :class:`Structure` reads and writes Minecraft's ``.nbt``
   structure format, so a captured box becomes a file the game accepts, and a
   file saved by a structure block can be read back and edited in Python.
3. **Restore** — a :class:`StructureLibrary` writes those files into a
   datapack's ``data/<ns>/structures/`` and hands out the ``ns:name`` ids that
   the ``place`` effect uses::

       with builder.add_state("BUILT") as built:
           built.enter.place(library.id("dungeon_room"), BlockPos(0, 64, 0))

   which lowers to ``place template grimmcraft:dungeon_room 0 64 0``.

``place`` is part of the shared command vocabulary (``grimmcraft-control``), so
the compiler renders it, the decompiler reads it back, and it round-trips like
any other effect.

    from grimmcraft_structures import StructureLibrary, capture
    from grimmcraft_core import BlockPos

    room = capture("saves/world", BlockPos(0, 64, 0), BlockPos(8, 70, 8))
    library = StructureLibrary("dungeon")
    library.add("room", room.without("minecraft:air"))
    library.write_into("dist/dungeon")
"""

from __future__ import annotations

from grimmcraft_structures.capture import WorldBlockReader, capture
from grimmcraft_structures.library import STRUCTURES_DIR, StructureLibrary
from grimmcraft_structures.structure import (
    DEFAULT_DATA_VERSION,
    VOID_AIR,
    Block,
    BlockState,
    Structure,
)

__all__ = [
    "Structure",
    "BlockState",
    "Block",
    "StructureLibrary",
    "STRUCTURES_DIR",
    "capture",
    "WorldBlockReader",
    "DEFAULT_DATA_VERSION",
    "VOID_AIR",
]
