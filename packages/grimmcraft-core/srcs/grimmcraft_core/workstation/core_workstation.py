"""The :class:`CoreWorkstation` base for placeable, interactable stations."""

# Includes
from __future__ import annotations

from grimmclub_standardlib import ABC, TYPE_CHECKING, dataclass
from grimmcraft_core.coordinates import Coordinates
from grimmcraft_data import VillagerProfession, profession_for_workstation
from grimmcraft_data.block import Block

if TYPE_CHECKING:
    from grimmcraft_core.entity.core_entity import CoreEntity

# Classes
@dataclass(kw_only=True)
class CoreWorkstation(ABC):
    """A block a player interacts with to open a station (crafting, smelting, …).

    ``block_type`` is a :class:`grimmcraft_data.block.Block` member.  Satisfies the
    ``Positioned`` protocol (:attr:`position`) and the ``Interactable`` protocol
    (:meth:`interact`).

    A subclass supplies its ``block_type`` and whatever behaviour the station
    has; :meth:`menu_title` is derived from the block and only overridden where
    the game's own title differs.
    """

    block_type: Block
    position: Coordinates
    current_user: CoreEntity | None = None

    @property
    def job_site_profession(self) -> VillagerProfession | None:
        """The villager profession this station creates, or ``None``.

        Read from ``grimmcraft_data``'s generated registry rather than declared
        per subclass, so a station cannot disagree with the data about what it
        employs. Of the stations modelled here, a brewing stand makes a cleric
        and a stonecutter a mason; the rest employ nobody.
        """
        return profession_for_workstation(self.block_type)

    @property
    def is_job_site(self) -> bool:
        """Whether standing this block near a villager gives them a profession."""
        return self.job_site_profession is not None

    def menu_title(self) -> str:
        """The display title shown when the station's menu opens.

        Derived from :attr:`block_type` — ``minecraft:crafting_table`` becomes
        ``"Crafting Table"`` — which is right for most stations, so a subclass
        only writes this out when the game disagrees. The enchanting table does:
        its menu is titled ``"Enchant"``, not ``"Enchanting Table"``.

        Overridable rather than abstract, so the one station that differs is
        visible as an override instead of being lost among four identical
        siblings that all restate the obvious.
        """
        return self.block_type.string_id.split(":", 1)[-1].replace("_", " ").title()

    def interact(self, actor: CoreEntity) -> None:
        """Open the station for ``actor`` (records the current user)."""
        self.current_user = actor
