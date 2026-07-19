"""The :class:`BrewingStand` workstation (potions) — behavioural stub."""

from __future__ import annotations

from grimmclub_standardlib import dataclass, field
from grimmcraft_core.item.core_item import CoreItem
from grimmcraft_core.workstation.core_workstation import CoreWorkstation
from grimmcraft_data.block import Block

BREWING_BOTTLE_SLOTS = 3


def _empty_bottles() -> list[CoreItem | None]:
    return [None] * BREWING_BOTTLE_SLOTS


@dataclass(kw_only=True)
class BrewingStand(CoreWorkstation):
    """Brews an ingredient into up to three potion bottles. Brewing TBD."""

    block_type: Block = Block.BREWING_STAND
    ingredient: CoreItem | None = None
    fuel: CoreItem | None = None
    bottles: list[CoreItem | None] = field(default_factory=_empty_bottles)

    def menu_title(self) -> str:
        return "Brewing Stand"

    def brew(self) -> None:
        """Run one brewing cycle over the loaded bottles (not yet implemented)."""
        raise NotImplementedError("brewing is not implemented yet")
