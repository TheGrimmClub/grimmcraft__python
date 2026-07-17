"""A written book item."""

from __future__ import annotations

from dataclasses import dataclass, field

from grimmcraft_core.item.core_item import CoreItem
from grimmcraft_data.item import Item


@dataclass(kw_only=True)
class Book(CoreItem):
    """A writable/written book carrying title, author and page text.

    Defaults to :attr:`Item.WRITABLE_BOOK`; set ``item_type=Item.WRITTEN_BOOK``
    once it has been signed.  Books never stack, so ``count`` stays 1.
    """

    item_type: Item = Item.WRITABLE_BOOK
    title: str = ""
    author: str | None = None
    pages: list[str] = field(default_factory=list)

    @property
    def is_signed(self) -> bool:
        """True once the book has become a written (signed) book."""
        return self.item_type is Item.WRITTEN_BOOK
