"""The barrel: 27 slots that never becomes 54, and a fisherman\'s workbench.

# Classes:

- `Barrel()`: storage that is also a villager job site

A barrel differs from a chest in three ways, and only one of them is storage:

- it **cannot be doubled**, which is why it is a sibling of
  :class:`~grimmcraft_core.item.chest.Chest` rather than a variant of it —
  there is no ``double`` field here to set;
- it is a **villager job site**: a barrel near an unemployed villager makes a
  fisherman, which no chest does (see ``grimmcraft_data.VillagerWorkstation``);
- it opens with a block above it, where a chest does not. That is placement
  behaviour rather than storage behaviour, and is not modelled here.
"""

# Includes
from __future__ import annotations

# Includes standard
from grimmclub_standardlib import dataclass

# Includes internal
from grimmcraft_core.item.storage import StorageBlock
from grimmcraft_data.item import Item


# Main Class
@dataclass(kw_only=True)
class Barrel(StorageBlock):
    """A barrel: 27 slots, always, and the block that employs a fisherman."""

    item_type: Item = Item.BARREL
