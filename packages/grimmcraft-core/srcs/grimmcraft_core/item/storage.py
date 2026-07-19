"""The shared behaviour of a block you can put things in.

# Classes:

- `PlaceableBlock`: an item that can be stood up in the world and opened
- `StorageBlock`: a placeable block that holds its own items

# Why a base class rather than a "kind" field

Minecraft has one storage *behaviour* and several blocks that wear it: a chest,
a barrel, an ender chest, a trapped chest, seventeen shulker boxes. They differ
in ways that are mostly not about storage — whether they can be doubled, whether
a villager takes a job from one, whether opening needs air above.

Putting those differences in a field on one class means every instance carries
every other block's options, and the ones that do not apply have to be rejected:
``Chest(kind=BARREL, double=True)`` would need to raise. A subclass simply does
not have the field. A barrel cannot be double because there is nothing to set,
which is a stronger guarantee than a check, and it needs no test to prove.

What is genuinely shared — slots, placement, who opened it last — lives here.

# What this deliberately does not model

:attr:`position` is a block position, so this covers storage that sits still.
Chest boats, chest minecarts and the chested horses carry inventories at an
*entity*, which is a different thing and not a subclass of this one. See
``PROMPT__VILLAGER_REGISTRIES.md`` — a structure capture that walks blocks loses
them silently today.
"""

# Includes
from __future__ import annotations

# Includes standard
from grimmclub_standardlib import TYPE_CHECKING, ClassVar, Iterator, dataclass, field

# Includes internal
from grimmcraft_core.coordinates import Coordinates
from grimmcraft_core.item.core_item import CoreItem, SlotContainer
from grimmcraft_data import VillagerProfession, profession_for_workstation

if TYPE_CHECKING:
    from grimmcraft_core.entity.core_entity import CoreEntity

# Constants
#: The capacity almost every storage block shares; only a double chest differs.
STANDARD_SLOTS = 27


# Classes
@dataclass(kw_only=True)
class PlaceableBlock(CoreItem):
    """An item that can be stood up in the world and opened.

    Carried in an inventory it has ``position is None``; placed in the world it
    gains :class:`Coordinates`. Interacting satisfies ``Interactable``.

    Separate from :class:`StorageBlock` because not every openable block holds
    its own items: an ender chest is a *view* onto storage kept elsewhere, so it
    is placeable and openable without being a container.
    """

    position: Coordinates | None = None
    last_opened_by: CoreEntity | None = None

    @property
    def is_placed(self) -> bool:
        """True when the block has been placed in the world."""
        return self.position is not None

    def place(self, position: Coordinates) -> None:
        """Place the block at ``position`` in the world."""
        self.position = position

    def break_block(self) -> None:
        """Take the block back out of the world.

        The counterpart to :meth:`place`. What happens to any contents is the
        subclass's business — a chest would drop them, an ender chest has none
        of its own to drop.
        """
        self.position = None

    def interact(self, actor: CoreEntity) -> None:
        """Open the block for ``actor`` (records the most recent viewer)."""
        self.last_opened_by = actor


# Main Class
@dataclass(kw_only=True)
class StorageBlock(PlaceableBlock):
    """A placeable block that holds its own items.

    Storage satisfies the ``Container`` protocol.
    """

    #: Slots this kind of block holds. Subclasses that vary at runtime — only
    #: the chest, so far — override :attr:`slot_count` instead.
    slots_held: ClassVar[int] = STANDARD_SLOTS

    # Derived from slot_count, so not a constructor argument: accepting a
    # container would let the size and the contents disagree.
    _contents: SlotContainer = field(init=False)

    def __post_init__(self) -> None:
        super().__post_init__()
        self._contents = SlotContainer(self.slot_count)

    @property
    def slot_count(self) -> int:
        """How many slots this instance has, before the container is built."""
        return self.slots_held

    @property
    def job_site_profession(self) -> VillagerProfession | None:
        """The villager profession this block creates, or ``None``.

        Read from ``grimmcraft_data``'s generated registry rather than declared
        per subclass, so a block cannot disagree with the data about what it
        employs. Of the storage blocks only a barrel does, making a fisherman.
        """
        # By id rather than by member: the lookup takes a Block, and this is an
        # Item. They share the namespaced id, which is what the lookup reads.
        return profession_for_workstation(self.item_type.string_id)

    @property
    def is_job_site(self) -> bool:
        """Whether standing this block near a villager gives them a profession."""
        return self.job_site_profession is not None

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
