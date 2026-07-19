"""A :class:`StructureLibrary` — the structures a datapack ships and places.

Minecraft reads structure templates from ``data/<namespace>/structures/<name>.nbt``
and places them by the id ``namespace:name``. This class holds that mapping, so
a machine can say ``place(library.id("dungeon_room"))`` without anyone writing
the path or the id by hand, and the files land in the right place at emit time.

The library deliberately does *not* go through the compiler's ``Resource`` IR:
that models JSON documents, and a structure is gzipped binary NBT. Instead
:meth:`write_into` drops the files into an already-emitted datapack tree.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from grimmcraft_structures.structure import Structure

#: The datapack sub-folder structures live in. Unlike ``function``/``loot_table``,
#: this name did *not* change in the 1.21 singular-folder rename — it was already
#: ``structures`` and stayed there.
STRUCTURES_DIR = "structures"


@dataclass(slots=True)
class StructureLibrary:
    """Named structures belonging to one datapack namespace."""

    namespace: str = "grimmcraft"
    structures: dict[str, Structure] = field(default_factory=dict)

    def add(self, name: str, structure: Structure) -> str:
        """Register ``structure`` under ``name``; return its ``ns:name`` id."""
        self.structures[name] = structure
        return self.id(name)

    def id(self, name: str) -> str:
        """The template id Minecraft places by — ``namespace:name``."""
        return f"{self.namespace}:{name}"

    def load(self, name: str, path: str | Path) -> str:
        """Read a ``.nbt`` file and register it under ``name``."""
        return self.add(name, Structure.read(path))

    def load_directory(self, directory: str | Path) -> list[str]:
        """Register every ``.nbt`` file in ``directory``, named after each file."""
        return [
            self.load(path.stem, path)
            for path in sorted(Path(directory).glob("*.nbt"))
        ]

    def path_for(self, name: str, pack_root: str | Path) -> Path:
        """Where ``name`` is written inside a datapack tree."""
        return (
            Path(pack_root) / "data" / self.namespace / STRUCTURES_DIR / f"{name}.nbt"
        )

    def write_into(self, pack_root: str | Path) -> list[Path]:
        """Write every structure into an emitted datapack; return the paths.

        Call this *after* ``compile_machines`` has written the pack — the
        compiler owns the tree, this only adds files it does not model.
        """
        written: list[Path] = []
        for name, structure in self.structures.items():
            destination = self.path_for(name, pack_root)
            structure.write(destination)
            written.append(destination)
        return written

    def __len__(self) -> int:
        return len(self.structures)

    def __contains__(self, name: object) -> bool:
        return name in self.structures
