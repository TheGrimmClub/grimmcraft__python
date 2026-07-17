"""Items: the :class:`CoreItem` base, containers, and concrete item types."""

from __future__ import annotations

from grimmcraft_core.item.book import Book
from grimmcraft_core.item.chest import Chest
from grimmcraft_core.item.core_item import CoreItem, Inventory, SlotContainer

__all__ = [
    "CoreItem",
    "SlotContainer",
    "Inventory",
    "Book",
    "Chest",
]
