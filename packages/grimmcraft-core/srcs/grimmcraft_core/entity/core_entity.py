"""The :class:`CoreEntity` base for every live actor in the world."""

# Includes
from __future__ import annotations

from grimmclub_standardlib import ABC, UUID, dataclass, field, uuid4
from grimmcraft_core.coordinates import Coordinates
from grimmcraft_data.entity import Entity


# Classes
@dataclass(kw_only=True)
class CoreEntity(ABC):
    """A mutable, positioned actor with health — the shared base for players,
    mobs and NPCs.

    ``entity_type`` is a :class:`grimmcraft_data.entity.Entity` enum member and is
    never re-declared here.  The class is abstract: instantiate a concrete
    subclass.  Satisfies the ``Positioned`` protocol via :attr:`position`.
    """

    entity_type: Entity
    position: Coordinates
    uuid: UUID = field(default_factory=uuid4)
    name: str | None = None
    health: float = 20.0
    max_health: float = 20.0

    def __post_init__(self) -> None:
        if self.max_health <= 0:
            raise ValueError(f"max_health must be positive, got {self.max_health}")
        # Clamp health into the valid band rather than rejecting out-of-range input.
        self.health = max(0.0, min(self.health, self.max_health))

    @property
    def is_alive(self) -> bool:
        """True while the entity has health remaining."""
        return self.health > 0

    def move_to(self, position: Coordinates) -> None:
        """Walk/relocate the entity to ``position`` (same as :meth:`teleport`
        here; kept distinct so subclasses can animate movement differently)."""
        self.position = position

    def teleport(self, position: Coordinates) -> None:
        """Instantly place the entity at ``position``."""
        self.position = position

    def distance_to(self, other: CoreEntity) -> float:
        """Euclidean distance to another entity, in blocks."""
        return self.position.distance_to(other.position)

    def damage(self, amount: float) -> None:
        """Apply ``amount`` of damage, flooring health at 0."""
        if amount < 0:
            raise ValueError(f"damage amount must be non-negative, got {amount}")
        self.health = max(0.0, self.health - amount)

    def heal(self, amount: float) -> None:
        """Restore ``amount`` of health, capped at :attr:`max_health`."""
        if amount < 0:
            raise ValueError(f"heal amount must be non-negative, got {amount}")
        self.health = min(self.max_health, self.health + amount)
