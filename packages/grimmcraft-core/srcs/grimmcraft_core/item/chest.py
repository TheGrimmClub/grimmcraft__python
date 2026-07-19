"""The chest: the one storage block that can be doubled.

# Classes:

- `Chest( double )`: 27 slots, or 54 when doubled
"""

from __future__ import annotations

# Includes standard
from grimmclub_standardlib import dataclass

# Includes internal
from grimmcraft_core.item.storage import STANDARD_SLOTS, StorageBlock
from grimmcraft_data.item import Item

# Constants
SINGLE_CHEST_SLOTS = STANDARD_SLOTS
DOUBLE_CHEST_SLOTS = STANDARD_SLOTS * 2


# Main Class
@dataclass(kw_only=True)
class Chest(StorageBlock):
    """A chest, optionally the double-wide kind.

    ``double`` lives here rather than on :class:`StorageBlock` because no other
    storage block can be doubled — a barrel, an ender chest and a shulker box
    are always 27 slots, and giving them the field would mean rejecting it.
    """

    item_type: Item = Item.CHEST
    double: bool = False

    @property
    def slot_count(self) -> int:
        """54 when doubled, 27 otherwise — read once, when the chest is built."""
        return DOUBLE_CHEST_SLOTS if self.double else SINGLE_CHEST_SLOTS
