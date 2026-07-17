"""The :class:`CoreWorkstation` base for placeable, interactable stations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING

from grimmcraft_core.coordinates import Coordinates
from grimmcraft_data.block import Block

if TYPE_CHECKING:
    from grimmcraft_core.entity.core_entity import CoreEntity


@dataclass(kw_only=True)
class CoreWorkstation(ABC):
    """A block a player interacts with to open a station (crafting, smelting, …).

    ``block_type`` is a :class:`grimmcraft_data.block.Block` member.  Satisfies the
    ``Positioned`` protocol (:attr:`position`) and the ``Interactable`` protocol
    (:meth:`interact`).  Abstract: subclasses supply a :meth:`menu_title`.
    """

    block_type: Block
    position: Coordinates
    current_user: CoreEntity | None = None

    @abstractmethod
    def menu_title(self) -> str:
        """The display title shown when the station's menu opens."""

    def interact(self, actor: CoreEntity) -> None:
        """Open the station for ``actor`` (records the current user)."""
        self.current_user = actor
