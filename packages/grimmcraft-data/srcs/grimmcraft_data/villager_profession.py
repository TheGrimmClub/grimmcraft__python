"""Auto-generated. Do not edit by hand; regenerate with
_generate/advanced_villager.py.
Minecraft Java Edition 1.21.11 — 15 villager professions.

Each member's .value and .string_id are the namespaced id; .display_name is
the human label; .workstation is the namespaced id of the block that gives a
villager this profession, or None for professions with no job site.

The profession list comes from Mojang's language.json. The workstation
mapping is curated (Mojang publishes it only in Java source) and verified
against language.json and the Block enum at generation time."""

from __future__ import annotations

from enum import Enum


class VillagerProfession(Enum):
    def __new__(cls, string_id: str, display_name: str, workstation: str | None):
        obj = object.__new__(cls)
        obj._value_ = string_id
        obj.string_id = string_id
        obj.display_name = display_name
        obj.workstation = workstation
        return obj

    ARMORER = ("minecraft:armorer", "Armorer", "minecraft:blast_furnace")
    BUTCHER = ("minecraft:butcher", "Butcher", "minecraft:smoker")
    CARTOGRAPHER = ("minecraft:cartographer", "Cartographer", "minecraft:cartography_table")
    CLERIC = ("minecraft:cleric", "Cleric", "minecraft:brewing_stand")
    FARMER = ("minecraft:farmer", "Farmer", "minecraft:composter")
    FISHERMAN = ("minecraft:fisherman", "Fisherman", "minecraft:barrel")
    FLETCHER = ("minecraft:fletcher", "Fletcher", "minecraft:fletching_table")
    LEATHERWORKER = ("minecraft:leatherworker", "Leatherworker", "minecraft:cauldron")
    LIBRARIAN = ("minecraft:librarian", "Librarian", "minecraft:lectern")
    MASON = ("minecraft:mason", "Mason", "minecraft:stonecutter")
    NITWIT = ("minecraft:nitwit", "Nitwit", None)
    NONE = ("minecraft:none", "Villager", None)
    SHEPHERD = ("minecraft:shepherd", "Shepherd", "minecraft:loom")
    TOOLSMITH = ("minecraft:toolsmith", "Toolsmith", "minecraft:smithing_table")
    WEAPONSMITH = ("minecraft:weaponsmith", "Weaponsmith", "minecraft:grindstone")


def profession_for_workstation(block) -> VillagerProfession | None:
    """The profession a villager takes from ``block``, or None."""
    wanted = getattr(block, "string_id", block)
    for profession in VillagerProfession:
        if profession.workstation == wanted:
            return profession
    return None


def workstation_for_profession(profession) -> str | None:
    """The namespaced block id that creates ``profession``, or None."""
    wanted = getattr(profession, "string_id", profession)
    for candidate in VillagerProfession:
        if candidate.string_id == wanted:
            return candidate.workstation
    return None
