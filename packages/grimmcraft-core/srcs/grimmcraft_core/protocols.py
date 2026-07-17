"""Small structural interfaces shared by composition rather than inheritance.

These are :class:`typing.Protocol` types: any object with the right shape
satisfies them, so entities, items and workstations can advertise capabilities
(being positioned, holding items, being interactable) without a common base
class.  Kept dependency-light on purpose — only :mod:`coordinates` is imported at
runtime; concrete domain types are referenced lazily to avoid import cycles.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from grimmcraft_core.coordinates import Coordinates

if TYPE_CHECKING:
    from grimmcraft_core.entity.core_entity import CoreEntity
    from grimmcraft_core.item.core_item import CoreItem


@runtime_checkable
class Positioned(Protocol):
    """Anything that occupies a place in the world."""

    position: Coordinates


@runtime_checkable
class Container(Protocol):
    """Anything that holds a fixed number of item slots."""

    slots: list[CoreItem | None]
    capacity: int

    def add(self, item: CoreItem) -> bool:
        """Place ``item`` in the first free slot; return whether it fit."""
        ...

    def remove(self, slot: int) -> CoreItem | None:
        """Take the item out of ``slot`` (leaving it empty) and return it."""
        ...

    @property
    def is_full(self) -> bool:
        """True when no slot is free."""
        ...

    def __iter__(self) -> Iterator[CoreItem | None]: ...


@runtime_checkable
class Interactable(Protocol):
    """Anything a player (or other entity) can right-click / use."""

    def interact(self, actor: CoreEntity) -> None:
        """React to ``actor`` interacting with this object."""
        ...
