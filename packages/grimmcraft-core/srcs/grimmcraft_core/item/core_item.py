"""The :class:`CoreItem` base plus the slot-container machinery items live in.

An item is a *live* stack (its ``count`` changes as it is split and merged), so it
is a mutable dataclass.  :class:`SlotContainer` is the reusable implementation of
the :class:`~grimmcraft_core.protocols.Container` protocol shared by player
inventories and placed chests.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Any

from grimmcraft_data.item import Item


def _stack_limit(item_type: Item) -> int:
    """Maximum stack size for ``item_type``, defaulting to 64 when unknown."""
    size = getattr(item_type, "stack_size", None)
    return int(size) if size else 64


@dataclass(kw_only=True)
class CoreItem:
    """A stack of one item kind.

    ``item_type`` is a :class:`grimmcraft_data.item.Item` enum member — the source
    of truth for the item's identity and stack limit — never re-declared here.
    ``metadata`` is a free-form NBT-ish bag for per-stack data (enchantments,
    custom name, …).
    """

    item_type: Item
    count: int = 1
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.count < 0:
            raise ValueError(f"item count must be non-negative, got {self.count}")
        if self.count > self.stack_size:
            raise ValueError(
                f"{self.item_type.name} count {self.count} exceeds stack size {self.stack_size}"
            )

    @property
    def stack_size(self) -> int:
        """The largest number of this item that may share one slot."""
        return _stack_limit(self.item_type)

    def can_stack_with(self, other: CoreItem) -> bool:
        """Whether ``other`` may merge into this stack (same kind, same metadata)."""
        return (
            self.stack_size > 1
            and self.item_type is other.item_type
            and self.metadata == other.metadata
        )

    def split(self, n: int) -> CoreItem:
        """Remove ``n`` items and return them as a new stack.

        Raises ``ValueError`` if ``n`` is not between 1 and the current count.
        """
        if not 1 <= n <= self.count:
            raise ValueError(f"cannot split {n} from a stack of {self.count}")
        self.count -= n
        return CoreItem(item_type=self.item_type, count=n, metadata=dict(self.metadata))


class SlotContainer:
    """A fixed-capacity grid of item slots implementing the ``Container`` protocol.

    Free slots hold ``None``.  This is the shared storage used by inventories and
    chests; compose or subclass it rather than reimplementing slot bookkeeping.
    """

    def __init__(self, capacity: int) -> None:
        if capacity <= 0:
            raise ValueError(f"container capacity must be positive, got {capacity}")
        self.capacity = capacity
        self.slots: list[CoreItem | None] = [None] * capacity

    def add(self, item: CoreItem) -> bool:
        """Merge ``item`` into a matching stack or the first free slot.

        Returns ``True`` if it was stored, ``False`` if the container was full.
        """
        for existing in self.slots:
            if existing is not None and existing.can_stack_with(item):
                room = existing.stack_size - existing.count
                if room >= item.count:
                    existing.count += item.count
                    return True
        for slot, existing in enumerate(self.slots):
            if existing is None:
                self.slots[slot] = item
                return True
        return False

    def remove(self, slot: int) -> CoreItem | None:
        """Take the item out of ``slot`` (leaving it empty) and return it."""
        if not 0 <= slot < self.capacity:
            raise IndexError(f"slot {slot} out of range 0..{self.capacity - 1}")
        item = self.slots[slot]
        self.slots[slot] = None
        return item

    @property
    def is_full(self) -> bool:
        """True when every slot is occupied."""
        return all(slot is not None for slot in self.slots)

    def __iter__(self) -> Iterator[CoreItem | None]:
        return iter(self.slots)

    def __len__(self) -> int:
        return self.capacity


class Inventory(SlotContainer):
    """A player inventory — a :class:`SlotContainer` of a default 36 slots."""

    def __init__(self, capacity: int = 36) -> None:
        super().__init__(capacity)
