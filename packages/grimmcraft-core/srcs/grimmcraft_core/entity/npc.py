"""The :class:`Npc` entity — a trading, professioned villager.

Design choice: an NPC **is-a** :class:`Mob`.  Villagers are passive living
creatures, so they inherit health, AI and (non-)hostility from ``Mob`` and add
only the trading/profession layer on top.

`VillagerProfession` comes from ``grimmcraft-data``, where it is generated along
with the job-site block each profession needs — ``profession.workstation`` — so
placing a villager and placing the block that employs it use one source.
"""

# Includes
from __future__ import annotations

from grimmclub_standardlib import dataclass, field
from grimmcraft_core.entity.mob import Mob
from grimmcraft_data import VillagerProfession as VillagerProfession
from grimmcraft_data.entity import Entity
from grimmcraft_data.item import Item


# Classes
@dataclass(frozen=True, slots=True)
class Trade:
    """One villager trade offer: give ``gives`` in exchange for ``wants``."""

    gives: Item
    gives_count: int = 1
    wants: tuple[Item, ...] = ()
    max_uses: int = 16


@dataclass(kw_only=True)
class Npc(Mob):
    """A villager NPC with a profession, trade offers and dialogue lines."""

    entity_type: Entity = Entity.VILLAGER
    profession: VillagerProfession = VillagerProfession.NONE
    trades: list[Trade] = field(default_factory=list)
    dialogue: list[str] = field(default_factory=list)
