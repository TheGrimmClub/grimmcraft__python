"""Id validation backed by ``grimmcraft-data`` plus curated rename/deprecation tables.

``grimmcraft-data`` is the source of truth for which ``Block``/``Item``/``Entity``
ids exist in the bundled Minecraft version.  This module indexes those enums into
fast string-id lookups, adds ``difflib`` "did you mean" suggestions, and layers a
small hand-curated table of historic *renames* (so ``minecraft:grass`` can be
diagnosed as "renamed to ``short_grass``") and *deprecations*.
"""

from __future__ import annotations

import difflib
from dataclasses import dataclass
from enum import Enum
from functools import cache

from grimmcraft_data import Block, Entity, Item

#: The registry kinds the compiler validates.
Kind = str  # "block" | "item" | "entity"


@dataclass(frozen=True, slots=True)
class Rename:
    """A historic id rename: ``old`` became ``new`` in ``since`` (a version)."""

    old: str
    new: str
    since: str


# Curated renames (namespaced old id -> Rename). Extend as needed; these are the
# classic ones that trip people up. grimmcraft-data holds only the *current*
# version's ids, so this table supplies the "it was renamed" narrative.
_RENAMES: dict[str, Rename] = {
    "minecraft:grass": Rename("minecraft:grass", "minecraft:short_grass", "1.20.3"),
    "minecraft:scute": Rename("minecraft:scute", "minecraft:turtle_scute", "1.20.5"),
    "minecraft:grass_path": Rename(
        "minecraft:grass_path", "minecraft:dirt_path", "1.17"
    ),
    "minecraft:zombie_pigman": Rename(
        "minecraft:zombie_pigman", "minecraft:zombified_piglin", "1.16"
    ),
}

# Curated deprecations: ids that still exist in the bundled version but are
# discouraged -> the reason. (The bundled data cannot tell us "soft-deprecated",
# so this narrative lives here.) The entry below is illustrative but real.
_DEPRECATED: dict[str, str] = {
    "minecraft:cave_air": "internal/technical block; do not place it in datapacks",
}


def _string_ids(enum: type[Enum]) -> frozenset[str]:
    """Every ``.string_id`` in an enum, as a frozen set."""
    return frozenset(member.string_id for member in enum)  # type: ignore[attr-defined]


@cache
def _index() -> dict[Kind, frozenset[str]]:
    """Cached kind -> set-of-string-ids index built from the data enums."""
    return {
        "block": _string_ids(Block),
        "item": _string_ids(Item),
        "entity": _string_ids(Entity),
    }


def valid_ids(kind: Kind) -> frozenset[str]:
    """The set of valid namespaced ids for ``kind``."""
    return _index()[kind]


def exists(kind: Kind, string_id: str) -> bool:
    """Whether ``string_id`` is a real id of ``kind`` in the bundled version."""
    return string_id in valid_ids(kind)


def rename_of(string_id: str) -> Rename | None:
    """The :class:`Rename` record for ``string_id`` if it was historically renamed."""
    return _RENAMES.get(string_id)


def deprecation_of(string_id: str) -> str | None:
    """A deprecation reason for ``string_id`` if it is deprecated, else ``None``."""
    return _DEPRECATED.get(string_id)


def suggest(kind: Kind, string_id: str, *, limit: int = 1) -> list[str]:
    """Closest valid ids of ``kind`` to ``string_id`` (``difflib``), best first."""
    return difflib.get_close_matches(string_id, valid_ids(kind), n=limit, cutoff=0.6)
