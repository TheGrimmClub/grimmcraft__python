"""The :class:`Mob` entity — a non-player living creature."""

from __future__ import annotations

from dataclasses import dataclass, field

from grimmcraft_core.entity.core_entity import CoreEntity
from grimmcraft_core.item.core_item import CoreItem
from grimmcraft_data.entity import Entity

# `Entity.type` values that denote a living creature (i.e. a mob), as opposed to
# players, projectiles or misc "other" registry entries.
MOB_ENTITY_TYPES: frozenset[str] = frozenset(
    {"mob", "hostile", "passive", "animal", "ambient", "living"}
)


def _entity_kind(entity_type: Entity) -> str | None:
    """The ``type`` category of a data ``Entity`` (dynamically attached attr)."""
    return getattr(entity_type, "type", None)


@dataclass(kw_only=True)
class Mob(CoreEntity):
    """A living, non-player creature that may be hostile and may drop loot."""

    hostile: bool = False
    ai_enabled: bool = True
    drops: list[CoreItem] = field(default_factory=list)

    def __post_init__(self) -> None:
        super().__post_init__()
        kind = _entity_kind(self.entity_type)
        if kind is not None and kind not in MOB_ENTITY_TYPES:
            raise ValueError(
                f"{self.entity_type.name} is not a mob-category entity (type={kind!r})"
            )
