"""The :class:`Npc` entity — a trading, professioned villager.

Design choice: an NPC **is-a** :class:`Mob`.  Villagers are passive living
creatures, so they inherit health, AI and (non-)hostility from ``Mob`` and add
only the trading/profession layer on top.

`VillagerProfession` is defined locally as a stopgap: it is a Mojang *registry*
enum that ``grimmcraft-data`` does not yet ship (it requires the server data
report).  When ``grimmcraft_data.villager_profession`` is generated, swap this
import to reuse it and delete the local enum.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from grimmcraft_core.entity.mob import Mob
from grimmcraft_data.entity import Entity
from grimmcraft_data.item import Item


class VillagerProfession(Enum):
    """A villager's trade profession (placeholder for the data-package enum)."""

    NONE = "none"
    ARMORER = "armorer"
    BUTCHER = "butcher"
    CARTOGRAPHER = "cartographer"
    CLERIC = "cleric"
    FARMER = "farmer"
    FISHERMAN = "fisherman"
    FLETCHER = "fletcher"
    LEATHERWORKER = "leatherworker"
    LIBRARIAN = "librarian"
    MASON = "mason"
    NITWIT = "nitwit"
    SHEPHERD = "shepherd"
    TOOLSMITH = "toolsmith"
    WEAPONSMITH = "weaponsmith"


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
