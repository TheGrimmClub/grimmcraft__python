"""A chest: simultaneously a carriable item and a placeable storage block."""

# Includes
from __future__ import annotations

from grimmclub_standardlib import TYPE_CHECKING, Iterator, dataclass, field
from grimmcraft_core.coordinates import Coordinates
from grimmcraft_core.item.core_item import CoreItem, SlotContainer
from grimmcraft_data.item import Item

if TYPE_CHECKING:
    from grimmcraft_core.entity.core_entity import CoreEntity

# Constants
SINGLE_CHEST_SLOTS = 27
DOUBLE_CHEST_SLOTS = 54

# Classes
@dataclass(kw_only=True)
class Chest(CoreItem):
    """A chest that is both a :class:`CoreItem` and a container of items.

    A chest carried in an inventory has ``position is None``; once placed in the
    world it gains a :class:`Coordinates`.  Storage (``slots``, ``add``,
    ``remove`` …) satisfies the ``Container`` protocol and interacting opens it,
    satisfying ``Interactable``.
    """

    item_type: Item = Item.CHEST
    double: bool = False
    position: Coordinates | None = None
    last_opened_by: CoreEntity | None = None
    # Built in __post_init__ from `double`, so it is not a constructor argument:
    # the size is derived, and accepting a container would let the two disagree.
    # `init=False` also keeps it non-optional, which is what it really is — it
    # was `SlotContainer | None` purely to have a default, and every access then
    # had to be justified against a None that never happens.
    _contents: SlotContainer = field(init=False)

    def __post_init__(self) -> None:
        super().__post_init__()
        size = DOUBLE_CHEST_SLOTS if self.double else SINGLE_CHEST_SLOTS
        self._contents = SlotContainer(size)

    # --- placement -----------------------------------------------------------
    @property
    def is_placed(self) -> bool:
        """True when the chest has been placed in the world."""
        return self.position is not None

    def place(self, position: Coordinates) -> None:
        """Place the chest at ``position`` in the world."""
        self.position = position

    # --- Container protocol (delegated to the internal slot grid) ------------
    @property
    def slots(self) -> list[CoreItem | None]:
        return self._contents.slots

    @property
    def capacity(self) -> int:
        return self._contents.capacity

    def add(self, item: CoreItem) -> bool:
        """Store ``item``; return whether it fit."""
        return self._contents.add(item)

    def remove(self, slot: int) -> CoreItem | None:
        """Take the item out of ``slot`` and return it."""
        return self._contents.remove(slot)

    @property
    def is_full(self) -> bool:
        return self._contents.is_full

    def __iter__(self) -> Iterator[CoreItem | None]:
        return iter(self._contents)

    # --- Interactable protocol -----------------------------------------------
    def interact(self, actor: CoreEntity) -> None:
        """Open the chest for ``actor`` (records the most recent viewer)."""
        self.last_opened_by = actor
