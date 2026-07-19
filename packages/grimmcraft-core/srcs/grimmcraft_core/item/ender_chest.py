"""The ender chest: a window onto storage that lives somewhere else.

# Classes:

- `EnderStorage()`: owner id -> shared :class:`Inventory`
- `EnderChest( storage )`: a placeable block that opens one owner's inventory

# Functions:

- `ender_storage()`: the world's shared registry

# Why this is not a StorageBlock

Every other storage block *has* items. An ender chest does not: it shows the
items of whoever opened it, and every ender chest in the world shows the same
ones to the same player. Two consequences drop out of that, and they are the
whole behaviour:

- placing or breaking the block moves nothing, because the block never held
  anything to move;
- ``add(item)`` is a question this block cannot answer — add for *whom*? — so it
  is not offered. :class:`EnderChest` extends
  :class:`~grimmcraft_core.item.storage.PlaceableBlock`, which is placement and
  opening without a container, rather than
  :class:`~grimmcraft_core.item.storage.StorageBlock`.

:meth:`EnderChest.open` takes the player and returns their inventory, which is
the only honest signature for it.

# Ownership

Keyed on :attr:`~grimmcraft_core.entity.core_entity.CoreEntity.uuid`, matching
Minecraft and matching the only identity an entity here carries. There is no
team or party concept in this package to key on instead; if one arrives, this is
the single place that changes.

# Persistence

None, deliberately. ``grimmcraft-core`` is an in-memory domain model — nothing
in it serialises, and NBT belongs to ``grimmcraft-structures`` and
``grimmcraft-world``. A registry that saved itself would be the only thing here
that did.
"""

from __future__ import annotations

# Includes standard
from grimmclub_standardlib import TYPE_CHECKING, UUID, ClassVar, dataclass, field

# Includes internal
from grimmcraft_core.item.core_item import Inventory
from grimmcraft_core.item.storage import STANDARD_SLOTS, PlaceableBlock
from grimmcraft_data.item import Item

if TYPE_CHECKING:
    from grimmcraft_core.entity.core_entity import CoreEntity

# Classes
class EnderStorage:
    """Every owner's ender inventory, keyed by entity id.

    An inventory is created the first time an owner opens a chest, not when
    they join: a player who never opens one costs nothing, which is also how
    the game behaves.
    """

    #: Ender inventories are 27 slots in every version, and cannot be doubled.
    slots: ClassVar[int] = STANDARD_SLOTS

    def __init__(self) -> None:
        self._inventories: dict[UUID, Inventory] = {}

    @staticmethod
    def _key(owner: CoreEntity | UUID) -> UUID:
        """Accept an entity or a bare id, so callers need not unwrap."""
        return owner if isinstance(owner, UUID) else owner.uuid

    def for_owner(self, owner: CoreEntity | UUID) -> Inventory:
        """``owner``'s ender inventory, created empty on first access."""
        key = self._key(owner)
        if key not in self._inventories:
            self._inventories[key] = Inventory(self.slots)
        return self._inventories[key]

    def has_owner(self, owner: CoreEntity | UUID) -> bool:
        """Whether ``owner`` has ever opened an ender chest.

        Distinct from having an empty inventory, and it does not create one —
        useful precisely because :meth:`for_owner` does.
        """
        return self._key(owner) in self._inventories

    @property
    def owners(self) -> list[UUID]:
        """Every owner with an inventory, in first-access order."""
        return list(self._inventories)

    def clear(self) -> None:
        """Forget every inventory. Mainly for tests and for starting a new world."""
        self._inventories.clear()

    def __len__(self) -> int:
        return len(self._inventories)


#: The registry every ender chest uses unless told otherwise — this is what
#: makes two blocks in different places open the same items. Module-level
#: because "the world" is not modelled as an object here; pass an explicit
#: :class:`EnderStorage` to isolate one (a test, a second world).
_WORLD_ENDER_STORAGE = EnderStorage()


# Functions
def ender_storage() -> EnderStorage:
    """The shared, world-wide ender storage."""
    return _WORLD_ENDER_STORAGE


# Main Class
@dataclass(kw_only=True)
class EnderChest(PlaceableBlock):
    """A block that opens its viewer's ender inventory, wherever it stands.

    Two ender chests anywhere in the world open the same items for the same
    player, and hold nothing of their own — so breaking one drops nothing and
    loses nothing.
    """

    item_type: Item = Item.ENDER_CHEST
    #: Which registry to read. Defaults to the world's, which is what makes
    #: every ender chest a view of the same storage.
    storage: EnderStorage = field(default_factory=ender_storage)

    def open(self, player: CoreEntity | UUID) -> Inventory:
        """``player``'s ender inventory — the same one every ender chest shows."""
        return self.storage.for_owner(player)

    def interact(self, actor: CoreEntity) -> None:
        """Open the chest for ``actor``, recording them as the most recent viewer."""
        super().interact(actor)
        self.open(actor)

    def break_block(self) -> None:
        """Take the block back. Contents are untouched: it never had any.

        Overridden only to be explicit. A chest breaking would have to decide
        what happens to its items; this one has nothing to decide.
        """
        super().break_block()
