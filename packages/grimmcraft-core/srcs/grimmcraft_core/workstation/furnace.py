"""The :class:`Furnace` workstation (smelting) — behavioural stub."""

# Includes
from __future__ import annotations

from grimmclub_standardlib import dataclass
from grimmcraft_core.item.core_item import CoreItem
from grimmcraft_core.workstation.core_workstation import CoreWorkstation
from grimmcraft_data.block import Block


# Classes
@dataclass(kw_only=True)
class Furnace(CoreWorkstation):
    """Smelts an input with a fuel into an output. Slots exposed; smelting TBD."""

    block_type: Block = Block.FURNACE
    input: CoreItem | None = None
    fuel: CoreItem | None = None
    output: CoreItem | None = None


    def smelt(self) -> CoreItem | None:
        """Advance smelting and return the produced item (not yet implemented)."""
        raise NotImplementedError("furnace smelting is not implemented yet")
