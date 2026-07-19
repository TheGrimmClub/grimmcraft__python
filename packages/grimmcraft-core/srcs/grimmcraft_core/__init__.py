"""Core domain model for grimmcraft: entities, items, workstations and the
world primitives (coordinates, protocols, scoreboard, clock) they share.

Enum *types* (``Block``, ``Item``, ``Entity``, …) come from ``grimmcraft-data``
and are used, never re-declared, here.
"""

from __future__ import annotations

from grimmcraft_core.clock import ClockEvent, ClockFire, MinecraftClock, TimeOfDay
from grimmcraft_core.coordinates import BlockPos, Coordinates, Direction
from grimmcraft_core.entity import (
    CoreEntity,
    GameMode,
    Mob,
    Npc,
    Player,
    Trade,
    VillagerProfession,
)
from grimmcraft_core.item import Book, Chest, CoreItem, Inventory, SlotContainer
from grimmcraft_core.protocols import Container, Interactable, Positioned
from grimmcraft_core.scoreboard import ScoreBoard
from grimmcraft_core.workstation import (
    Anvil,
    BrewingStand,
    CoreWorkstation,
    CraftingTable,
    EnchantingTable,
    Furnace,
)

# Registry enum *types* come from grimmcraft-data; re-export them under clearer
# "…Type" names so domain code imports them from here alongside the other core
# world types (``BlockType.STONE`` reads better than ``Block.STONE``).
from grimmcraft_data import Block as BlockType
from grimmcraft_data import Entity as EntityType
from grimmcraft_data import Item as ItemType

__all__ = [
    # registry enum types (re-exported from grimmcraft-data)
    "BlockType",
    "ItemType",
    "EntityType",
    # world primitives
    "Coordinates",
    "BlockPos",
    "Direction",
    "Positioned",
    "Container",
    "Interactable",
    "ScoreBoard",
    "MinecraftClock",
    "TimeOfDay",
    "ClockEvent",
    "ClockFire",
    # entities
    "CoreEntity",
    "Player",
    "GameMode",
    "Mob",
    "Npc",
    "Trade",
    "VillagerProfession",
    # items
    "CoreItem",
    "SlotContainer",
    "Inventory",
    "Book",
    "Barrel",
    "Chest",
    "StorageBlock",
    # workstations
    "CoreWorkstation",
    "CraftingTable",
    "Furnace",
    "BrewingStand",
    "Anvil",
    "EnchantingTable",
    # misc
]
