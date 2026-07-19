"""Auto-generated. Do not edit by hand; regenerate with
_generate/advanced_villager.py.
Minecraft Java Edition 1.21.11 — 13 villager job sites.

The blocks that give a villager a profession. This is a different idea from
the workstations modelled in grimmcraft-core, which are the blocks a *player*
uses: only brewing_stand is both.

Each member's .value and .string_id are the namespaced block id;
.profession is the namespaced id of the profession it creates."""

from __future__ import annotations

from grimmclub_standardlib import TYPE_CHECKING, Enum

if TYPE_CHECKING:
    from .block import Block


class VillagerWorkstation(Enum):
    string_id: str
    profession: str

    def __new__(cls, string_id: str, profession: str) -> VillagerWorkstation:
        obj = object.__new__(cls)
        obj._value_ = string_id
        obj.string_id = string_id
        obj.profession = profession
        return obj

    BARREL = ("minecraft:barrel", "minecraft:fisherman")
    BLAST_FURNACE = ("minecraft:blast_furnace", "minecraft:armorer")
    BREWING_STAND = ("minecraft:brewing_stand", "minecraft:cleric")
    CARTOGRAPHY_TABLE = ("minecraft:cartography_table", "minecraft:cartographer")
    CAULDRON = ("minecraft:cauldron", "minecraft:leatherworker")
    COMPOSTER = ("minecraft:composter", "minecraft:farmer")
    FLETCHING_TABLE = ("minecraft:fletching_table", "minecraft:fletcher")
    GRINDSTONE = ("minecraft:grindstone", "minecraft:weaponsmith")
    LECTERN = ("minecraft:lectern", "minecraft:librarian")
    LOOM = ("minecraft:loom", "minecraft:shepherd")
    SMITHING_TABLE = ("minecraft:smithing_table", "minecraft:toolsmith")
    SMOKER = ("minecraft:smoker", "minecraft:butcher")
    STONECUTTER = ("minecraft:stonecutter", "minecraft:mason")


def workstation_for_block(block: Block | str) -> VillagerWorkstation | None:
    """The job site ``block`` is, or None if it is not one."""
    wanted = getattr(block, "string_id", block)
    for workstation in VillagerWorkstation:
        if workstation.string_id == wanted:
            return workstation
    return None
