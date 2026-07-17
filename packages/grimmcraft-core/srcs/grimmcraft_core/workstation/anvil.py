"""The :class:`Anvil` workstation (repair/rename) — behavioural stub."""

from __future__ import annotations

from dataclasses import dataclass

from grimmcraft_core.item.core_item import CoreItem
from grimmcraft_core.workstation.core_workstation import CoreWorkstation
from grimmcraft_data.block import Block


@dataclass(kw_only=True)
class Anvil(CoreWorkstation):
    """Combines/repairs/renames items for an XP cost. Combination logic TBD."""

    block_type: Block = Block.ANVIL
    left: CoreItem | None = None
    right: CoreItem | None = None
    rename_to: str | None = None

    def menu_title(self) -> str:
        return "Anvil"

    def combine(self) -> CoreItem | None:
        """Produce the combined/repaired result (not yet implemented)."""
        raise NotImplementedError("anvil combination is not implemented yet")
