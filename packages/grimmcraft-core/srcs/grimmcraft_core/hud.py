"""A heads-up display: a line assembled from whatever wants to be on it, plus
the waypoint compass that navigates towards a place.

# Classes:

- `Waypoint( name, position, symbol )`: somewhere worth going back to
- `Bearing( yaw, distance )`: the answer to "where is it from here?"
- `Compass( origin, facing )`: bearings and turn hints from a position
- `Hud()`: ordered segments rendered as one line

# Functions:

- `bearing_to(origin, target)`: the Minecraft yaw pointing at ``target``
- `compass_point(yaw)`: ``"N"``, ``"NE"``, … for a yaw
- `facing_direction(yaw)`: the nearest horizontal :class:`Direction`
- `turn_to(facing, yaw)`: signed degrees to turn, negative left

# Minecraft's yaw convention

This is the part worth reading twice, because it is not the compass convention
and getting it wrong points players the opposite way:

| yaw | faces | axis |
|-----|-------|------|
| 0   | south | +Z   |
| 90  | west  | -X   |
| 180 | north | -Z   |
| 270 | east  | +X   |

So yaw runs *clockwise from south*, while an ordinary compass bearing runs
clockwise from north. :func:`compass_point` converts, which is why it exists
rather than being a lookup a caller could inline.

Distances are horizontal: a waypoint 200 blocks away and 60 blocks up is 200
away, matching the in-game compass and the intuition of someone walking there.

# Why this module imports almost nothing

Like :mod:`grimmcraft_core.clock`, this must not import the things that display
on it. :class:`Hud` therefore accepts a string, a callable, or any object with a
``hud()`` method, so the clock and the player contribute to a HUD without this
module knowing they exist — and without either of them importing the other.
"""

from __future__ import annotations

# Includes standard
from grimmclub_standardlib import Callable, dataclass, field, math

# Includes internal
from grimmcraft_core.coordinates import Coordinates, Direction

# Constants
#: The eight compass points, clockwise from north.
COMPASS_POINTS = ("N", "NE", "E", "SE", "S", "SW", "W", "NW")

#: An arrow per compass point, clockwise from north — used for turn hints.
COMPASS_ARROWS = ("↑", "↗", "→", "↘", "↓", "↙", "←", "↖")

#: Yaw of each horizontal face, in Minecraft's convention.
_FACE_YAW: dict[Direction, float] = {
    Direction.SOUTH: 0.0,
    Direction.WEST: 90.0,
    Direction.NORTH: 180.0,
    Direction.EAST: 270.0,
}

#: How close a bearing must be, in blocks, to count as "arrived".
ARRIVAL_DISTANCE = 1.0


# Functions
def normalise_yaw(yaw: float) -> float:
    """Fold ``yaw`` into ``[-180, 180)``, the range Minecraft itself reports."""
    return (yaw + 180.0) % 360.0 - 180.0


def bearing_to(origin: Coordinates, target: Coordinates) -> float:
    """The Minecraft yaw that points from ``origin`` at ``target``.

    Vertical difference is ignored: this is where to *walk*, not where to look.
    """
    return normalise_yaw(math.degrees(math.atan2(-(target.x - origin.x), target.z - origin.z)))


def horizontal_distance(origin: Coordinates, target: Coordinates) -> float:
    """Distance ignoring height, which is what a compass and a walker care about."""
    return math.dist((origin.x, origin.z), (target.x, target.z))


def compass_heading(yaw: float) -> float:
    """Convert a Minecraft yaw to an ordinary compass bearing (0 = north).

    Minecraft measures clockwise from *south*; a compass measures clockwise from
    north. The two are half a turn apart.
    """
    return (yaw + 180.0) % 360.0


def compass_point(yaw: float) -> str:
    """The nearest of the eight compass points to ``yaw`` — ``"N"``, ``"NE"``, …"""
    return COMPASS_POINTS[round(compass_heading(yaw) / 45.0) % 8]


def facing_direction(yaw: float) -> Direction:
    """The nearest horizontal :class:`Direction` to ``yaw``.

    Only the four horizontal faces can be a heading; ``UP`` and ``DOWN`` are not
    somewhere you can walk.
    """
    return min(_FACE_YAW, key=lambda face: abs(turn_to(yaw, _FACE_YAW[face])))


def turn_to(facing: float, yaw: float) -> float:
    """Signed degrees to turn from ``facing`` to ``yaw`` — negative is left.

    Always the shorter way round, so the result is within ``[-180, 180)`` and a
    player is never told to spin 350 degrees rather than 10 the other way.
    """
    return normalise_yaw(yaw - facing)


# Classes
@dataclass(frozen=True, slots=True)
class Bearing:
    """Where something is from somewhere else: a yaw, a distance, and the words."""

    yaw: float
    distance: float
    facing: float | None = None

    @property
    def point(self) -> str:
        """The compass point to head for (``"NE"``)."""
        return compass_point(self.yaw)

    @property
    def direction(self) -> Direction:
        """The nearest horizontal face to head for."""
        return facing_direction(self.yaw)

    @property
    def has_arrived(self) -> bool:
        """Whether this is close enough to count as being there."""
        return self.distance <= ARRIVAL_DISTANCE

    @property
    def turn(self) -> float | None:
        """Signed degrees to turn, or ``None`` when the facing is unknown."""
        return None if self.facing is None else turn_to(self.facing, self.yaw)

    @property
    def arrow(self) -> str:
        """An arrow for the turn — ``↑`` ahead, ``→`` right — or the compass point.

        Without a facing there is no "left" or "right", so this falls back to
        the absolute direction rather than inventing a relative one.
        """
        turn = self.turn
        if turn is None:
            return COMPASS_ARROWS[round(compass_heading(self.yaw) / 45.0) % 8]
        return COMPASS_ARROWS[round(turn / 45.0) % 8]

    def __str__(self) -> str:
        if self.has_arrived:
            return "here"
        return f"{self.arrow} {self.point} {self.distance:.0f}m"


@dataclass(frozen=True, slots=True)
class Waypoint:
    """A named place worth navigating back to."""

    name: str
    position: Coordinates
    symbol: str = "⚑"

    def bearing_from(self, origin: Coordinates, facing: float | None = None) -> Bearing:
        """Where this waypoint is, seen from ``origin``."""
        return Bearing(
            yaw=bearing_to(origin, self.position),
            distance=horizontal_distance(origin, self.position),
            facing=facing,
        )

    def hud_from(self, origin: Coordinates, facing: float | None = None) -> str:
        """A HUD segment for navigating here: ``⚑ Home → NE 210m``."""
        return f"{self.symbol} {self.name} {self.bearing_from(origin, facing)}"


@dataclass
class Compass:
    """Bearings from a position, optionally with a facing so it can say turn.

    ``origin`` and ``facing`` are mutable: a compass is carried, so it moves.
    """

    origin: Coordinates
    facing: float | None = None
    waypoints: dict[str, Waypoint] = field(default_factory=dict)

    # --- waypoints -----------------------------------------------------------
    def mark(self, name: str, position: Coordinates, symbol: str = "⚑") -> Waypoint:
        """Record ``position`` as a waypoint called ``name`` and return it."""
        waypoint = Waypoint(name=name, position=position, symbol=symbol)
        self.waypoints[name] = waypoint
        return waypoint

    def mark_here(self, name: str, symbol: str = "⚑") -> Waypoint:
        """Record where the compass is now — the common case for "remember this"."""
        return self.mark(name, self.origin, symbol)

    def forget(self, name: str) -> None:
        """Remove a waypoint (no-op if it was never marked)."""
        self.waypoints.pop(name, None)

    # --- bearings ------------------------------------------------------------
    def to(self, target: Waypoint | Coordinates | str) -> Bearing:
        """The bearing to a waypoint, a position, or a waypoint's name."""
        if isinstance(target, str):
            if target not in self.waypoints:
                raise KeyError(f"no waypoint named {target!r}")
            target = self.waypoints[target]
        position = target.position if isinstance(target, Waypoint) else target
        return Bearing(
            yaw=bearing_to(self.origin, position),
            distance=horizontal_distance(self.origin, position),
            facing=self.facing,
        )

    def nearest(self) -> Waypoint | None:
        """The closest marked waypoint, or ``None`` when nothing is marked."""
        if not self.waypoints:
            return None
        return min(
            self.waypoints.values(),
            key=lambda waypoint: horizontal_distance(self.origin, waypoint.position),
        )

    def hud(self) -> str:
        """A HUD segment for the nearest waypoint, or the current heading."""
        nearest = self.nearest()
        if nearest is not None:
            return nearest.hud_from(self.origin, self.facing)
        if self.facing is None:
            return "🧭 —"
        return f"🧭 {compass_point(self.facing)}"


#: Anything a HUD can show: fixed text, something that produces text, or an
#: object that knows how to describe itself (the clock and the compass both do).
Segment = str | Callable[[], str] | object


@dataclass
class Hud:
    """An ordered set of segments rendered as one status line.

    Nothing here knows what a clock or a player is. A segment is a string, a
    callable returning one, or any object with a ``hud()`` method — so both can
    appear on the same line without this module importing either.
    """

    segments: list[Segment] = field(default_factory=list)
    separator: str = "  │  "

    def add(self, segment: Segment) -> Hud:
        """Append a segment; returns ``self`` so calls can be chained."""
        self.segments.append(segment)
        return self

    def clear(self) -> None:
        """Remove every segment."""
        self.segments.clear()

    @staticmethod
    def _render_one(segment: Segment) -> str:
        if isinstance(segment, str):
            return segment
        renderer = getattr(segment, "hud", None)
        if callable(renderer):
            return str(renderer())
        if callable(segment):
            return str(segment())
        return str(segment)

    def render(self) -> str:
        """The whole line, empty segments dropped so no stray separators appear."""
        parts = [text for text in map(self._render_one, self.segments) if text]
        return self.separator.join(parts)

    def __str__(self) -> str:
        return self.render()
