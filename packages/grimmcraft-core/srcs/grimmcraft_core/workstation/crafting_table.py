"""The 3x3 :class:`CraftingTable` workstation."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from grimmcraft_core.item.core_item import CoreItem
from grimmcraft_core.workstation.core_workstation import CoreWorkstation
from grimmcraft_data.block import Block

GRID_SIZE = 3

# A recipe resolver maps the current 3x3 grid to a crafted result (or None).
# Kept as an injectable seam so recipe data (e.g. grimmcraft_data.recipe) can be
# wired in later without hardcoding recipes in the core model.
RecipeResolver = Callable[[list[list[CoreItem | None]]], CoreItem | None]


def _empty_grid() -> list[list[CoreItem | None]]:
    return [[None] * GRID_SIZE for _ in range(GRID_SIZE)]


@dataclass(kw_only=True)
class CraftingTable(CoreWorkstation):
    """A crafting table exposing a 3x3 grid and a pluggable crafting step."""

    block_type: Block = Block.CRAFTING_TABLE
    grid: list[list[CoreItem | None]] = field(default_factory=_empty_grid)
    recipe_resolver: RecipeResolver | None = None

    def menu_title(self) -> str:
        return "Crafting Table"

    def place(self, item: CoreItem | None, row: int, col: int) -> None:
        """Put ``item`` (or ``None`` to clear) into grid cell ``(row, col)``."""
        if not (0 <= row < GRID_SIZE and 0 <= col < GRID_SIZE):
            raise ValueError(f"grid cell ({row}, {col}) out of range 0..{GRID_SIZE - 1}")
        self.grid[row][col] = item

    def clear(self) -> None:
        """Empty every cell of the grid."""
        self.grid = _empty_grid()

    def craft(self) -> CoreItem | None:
        """Resolve the current grid to a crafted item via :attr:`recipe_resolver`.

        Returns ``None`` when no resolver is wired or the layout matches nothing;
        core deliberately ships no hardcoded recipes.
        """
        if self.recipe_resolver is None:
            return None
        return self.recipe_resolver(self.grid)
