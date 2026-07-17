"""Workstations: the :class:`CoreWorkstation` base and concrete stations."""

from __future__ import annotations

from grimmcraft_core.workstation.anvil import Anvil
from grimmcraft_core.workstation.brewing_stand import BrewingStand
from grimmcraft_core.workstation.core_workstation import CoreWorkstation
from grimmcraft_core.workstation.crafting_table import CraftingTable
from grimmcraft_core.workstation.enchantment_table import EnchantingTable
from grimmcraft_core.workstation.furnace import Furnace

__all__ = [
    "CoreWorkstation",
    "CraftingTable",
    "Furnace",
    "BrewingStand",
    "Anvil",
    "EnchantingTable",
]
