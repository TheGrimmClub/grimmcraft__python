"""The :class:`Player` entity.

The game mode comes from :mod:`grimmcraft_core.game` — this module used to
define a second, identical ``GameMode`` enum beside it, so the workspace had two
spellings of the same four values.
"""

# Includes
from __future__ import annotations

from grimmclub_standardlib import dataclass, field
from grimmcraft_core.entity.core_entity import CoreEntity
from grimmcraft_core.game import GameModeType
from grimmcraft_core.item.core_item import Inventory
from grimmcraft_data.entity import Entity


# Classes
@dataclass(kw_only=True)
class Player(CoreEntity):
    """A human-controlled entity with an inventory, game mode and progression."""

    entity_type: Entity = Entity.PLAYER
    inventory: Inventory = field(default_factory=Inventory)
    gamemode: GameModeType = GameModeType.SURVIVAL
    xp_level: int = 0
    hunger: int = 20

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.entity_type is not Entity.PLAYER:
            raise ValueError(
                f"Player.entity_type must be Entity.PLAYER, got {self.entity_type.name}"
            )
        if self.xp_level < 0:
            raise ValueError(f"xp_level must be non-negative, got {self.xp_level}")
        if not 0 <= self.hunger <= 20:
            raise ValueError(f"hunger must be within 0..20, got {self.hunger}")
