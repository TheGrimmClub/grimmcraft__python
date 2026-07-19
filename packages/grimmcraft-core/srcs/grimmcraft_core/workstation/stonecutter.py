"""The :class:`Stonecutter` workstation: one input, many outputs, pick one.

# Classes:

- `Stonecutter( input, selected )`: cuts a block into one of its variants

Unlike a crafting table, a stonecutter takes a **single** input and offers
several results — stone gives slabs, stairs, bricks, chiselled stone and more —
of which the player picks one. There is no fuel and no waiting: choosing is the
whole interaction.

Like :class:`~grimmcraft_core.workstation.crafting_table.CraftingTable`, the
recipes are an injected seam rather than a table baked in here: core ships no
recipe data, so a resolver is supplied by whoever has it.
"""

# Includes
from __future__ import annotations

# Includes standard
from grimmclub_standardlib import Callable, dataclass

# Includes internal
from grimmcraft_core.item.core_item import CoreItem
from grimmcraft_core.workstation.core_workstation import CoreWorkstation
from grimmcraft_data.block import Block

# Types
#: Maps an input item to the variants it can be cut into, in menu order.
CutResolver = Callable[[CoreItem], list[CoreItem]]


# Main Class
@dataclass(kw_only=True)
class Stonecutter(CoreWorkstation):
    """A stonecutter: one input, a menu of variants, and the one chosen."""

    block_type: Block = Block.STONECUTTER
    input: CoreItem | None = None
    selected: int = 0
    cut_resolver: CutResolver | None = None

    def set_input(self, item: CoreItem | None) -> None:
        """Put ``item`` in (or ``None`` to clear), resetting the selection.

        The reset matters: the menu is rebuilt for the new block, so keeping an
        old index would silently select a different variant than the one the
        player was looking at.
        """
        self.input = item
        self.selected = 0

    def options(self) -> list[CoreItem]:
        """The variants the current input can be cut into, in menu order.

        Empty when nothing is in, or when no resolver is wired — core
        deliberately ships no recipes of its own.
        """
        if self.input is None or self.cut_resolver is None:
            return []
        return self.cut_resolver(self.input)

    def select(self, index: int) -> None:
        """Choose the variant at ``index`` of :meth:`options`."""
        available = self.options()
        if not 0 <= index < len(available):
            raise ValueError(
                f"no variant at index {index}: the input offers {len(available)}"
            )
        self.selected = index

    def cut(self) -> CoreItem | None:
        """Take the selected variant, consuming the input.

        Returns ``None`` when there is nothing to cut, which is the same answer
        as an unwired resolver — in both cases the machine has no result to give.
        """
        available = self.options()
        if not available:
            return None
        result = available[self.selected]
        self.set_input(None)
        return result
