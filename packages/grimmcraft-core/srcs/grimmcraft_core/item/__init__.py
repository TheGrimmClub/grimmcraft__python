"""Items: the :class:`CoreItem` base, containers, and concrete item types."""

from __future__ import annotations

from grimmcraft_core.item.barrel import Barrel
from grimmcraft_core.item.book import Book
from grimmcraft_core.item.chest import Chest
from grimmcraft_core.item.core_item import CoreItem, Inventory, SlotContainer
from grimmcraft_core.item.ender_chest import EnderChest, EnderStorage, ender_storage
from grimmcraft_core.item.storage import PlaceableBlock, StorageBlock

__all__ = [
    "CoreItem",
    "SlotContainer",
    "Inventory",
    "PlaceableBlock",
    "StorageBlock",
    "Book",
    "Chest",
    "Barrel",
    "EnderChest",
    "EnderStorage",
    "ender_storage",
]
