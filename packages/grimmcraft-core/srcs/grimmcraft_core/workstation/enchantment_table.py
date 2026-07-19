"""The :class:`EnchantingTable` workstation — behavioural stub."""

# Includes
from __future__ import annotations

from grimmclub_standardlib import ClassVar, dataclass
from grimmcraft_core.item.core_item import CoreItem
from grimmcraft_core.workstation.core_workstation import CoreWorkstation
from grimmcraft_data.block import Block


# Classes
@dataclass(kw_only=True)
class EnchantingTable(CoreWorkstation):
    """Enchants an item using lapis and nearby bookshelves. Enchanting TBD."""

    #: The game titles this menu "Enchant", not "Enchanting Table".
    menu_name: ClassVar[str] = "Enchant"

    block_type: Block = Block.ENCHANTING_TABLE
    item: CoreItem | None = None
    lapis: CoreItem | None = None
    bookshelf_power: int = 0

    def enchant(self) -> CoreItem | None:
        """Apply an enchantment to the loaded item (not yet implemented)."""
        raise NotImplementedError("enchanting is not implemented yet")
