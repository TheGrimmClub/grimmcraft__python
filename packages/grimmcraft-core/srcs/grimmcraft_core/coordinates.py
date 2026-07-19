"""Positional value objects: world :class:`Coordinates`, integer :class:`BlockPos`
and the six-faced :class:`Direction`.

These are pure, immutable value objects with no dependencies on the rest of the
package, so every other module may import from here freely without risking a
circular import.
"""

# Includes
from __future__ import annotations

from grimmclub_standardlib import Enum, dataclass, math


# Types
class Direction(Enum):
    """One of the six block faces, in Minecraft's axis convention.

    North is ``-Z``, south ``+Z``, east ``+X``, west ``-X``, up ``+Y`` and down
    ``-Y``.  Use :attr:`delta` to step one block along the face and
    :attr:`opposite` to flip it.
    """

    NORTH = "north"
    SOUTH = "south"
    EAST = "east"
    WEST = "west"
    UP = "up"
    DOWN = "down"

    @property
    def delta(self) -> tuple[int, int, int]:
        """The unit ``(dx, dy, dz)`` step for moving one block along this face."""
        return _DIRECTION_DELTAS[self]

    @property
    def opposite(self) -> Direction:
        """The face pointing the other way (north <-> south, up <-> down, …)."""
        return _DIRECTION_OPPOSITES[self]


_DIRECTION_DELTAS: dict[Direction, tuple[int, int, int]] = {
    Direction.NORTH: (0, 0, -1),
    Direction.SOUTH: (0, 0, 1),
    Direction.EAST: (1, 0, 0),
    Direction.WEST: (-1, 0, 0),
    Direction.UP: (0, 1, 0),
    Direction.DOWN: (0, -1, 0),
}

_DIRECTION_OPPOSITES: dict[Direction, Direction] = {
    Direction.NORTH: Direction.SOUTH,
    Direction.SOUTH: Direction.NORTH,
    Direction.EAST: Direction.WEST,
    Direction.WEST: Direction.EAST,
    Direction.UP: Direction.DOWN,
    Direction.DOWN: Direction.UP,
}

# Classes
@dataclass(frozen=True, slots=True)
class Coordinates:
    """A continuous world position in block units (floats), hashable and immutable.

    Adding or subtracting another :class:`Coordinates` does component-wise vector
    maths; adding a :class:`Direction` steps one block along that face.
    """

    x: float
    y: float
    z: float

    def offset(self, dx: float = 0.0, dy: float = 0.0, dz: float = 0.0) -> Coordinates:
        """Return a new position shifted by ``(dx, dy, dz)``."""
        return Coordinates(self.x + dx, self.y + dy, self.z + dz)

    def __add__(self, other: Coordinates | Direction) -> Coordinates:
        if isinstance(other, Direction):
            dx, dy, dz = other.delta
            return self.offset(dx, dy, dz)
        if isinstance(other, Coordinates):
            return Coordinates(self.x + other.x, self.y + other.y, self.z + other.z)
        return NotImplemented

    def __sub__(self, other: Coordinates | Direction) -> Coordinates:
        if isinstance(other, Direction):
            dx, dy, dz = other.delta
            return self.offset(-dx, -dy, -dz)
        if isinstance(other, Coordinates):
            return Coordinates(self.x - other.x, self.y - other.y, self.z - other.z)
        return NotImplemented

    def distance_to(self, other: Coordinates) -> float:
        """Straight-line (Euclidean) distance to ``other`` in blocks."""
        return math.dist((self.x, self.y, self.z), (other.x, other.y, other.z))

    def manhattan_to(self, other: Coordinates) -> int:
        """Grid (taxicab) distance to ``other``, rounded to whole blocks."""
        return int(abs(self.x - other.x) + abs(self.y - other.y) + abs(self.z - other.z))

    def to_block_pos(self) -> BlockPos:
        """The block cell containing this position (floor of each axis)."""
        return BlockPos(math.floor(self.x), math.floor(self.y), math.floor(self.z))


@dataclass(frozen=True, slots=True)
class BlockPos:
    """A discrete block-grid position (integers), hashable and immutable."""

    x: int
    y: int
    z: int

    def to_coordinates(self) -> Coordinates:
        """The world position of this block's minimum (north-west-bottom) corner.

        This is the exact inverse of :meth:`Coordinates.to_block_pos`; add ``0.5``
        per axis yourself if you want the block centre.
        """
        return Coordinates(float(self.x), float(self.y), float(self.z))

    def offset(self, dx: int = 0, dy: int = 0, dz: int = 0) -> BlockPos:
        """Return a new block position shifted by ``(dx, dy, dz)``."""
        return BlockPos(self.x + dx, self.y + dy, self.z + dz)

    def step(self, direction: Direction) -> BlockPos:
        """Return the adjacent block one step along ``direction``."""
        dx, dy, dz = direction.delta
        return self.offset(dx, dy, dz)

    def neighbors(self) -> list[BlockPos]:
        """The six face-adjacent block positions, one per :class:`Direction`."""
        return [self.step(direction) for direction in Direction]
