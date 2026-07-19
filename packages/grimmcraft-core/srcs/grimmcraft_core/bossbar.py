"""Boss bars: the big labelled bar across the top of the screen.

# Classes:

- `BossBarColor`: the seven colours Minecraft allows
- `BossBarStyle`: solid, or notched into segments
- `BossBar( bar_id, name )`: one bar, its value and who sees it
- `BossBarSet()`: the world's bars, addressed by id

# What a boss bar is for here

:class:`~grimmcraft_core.scoreboard.ScoreBoard` counts things and
:class:`~grimmcraft_core.hud.Hud` writes a line of text. A boss bar is the third
display: one number, shown large, as a *proportion* of a maximum. That makes it
the right home for anything with a target — a timer running down, a boss's
health, a quest at three of five steps — and the wrong home for anything without
one.

It renders into a :class:`~grimmcraft_core.hud.Hud` like everything else, so a
bar and a clock can share a line while neither knows about the other.

# Validation follows the package's existing split

``value`` is **clamped** into ``0..max_value``, the way
:class:`~grimmcraft_core.entity.core_entity.CoreEntity` clamps health: a value
past the end is a bar that is full, not a program that stops. ``max_value`` is
**rejected** when it is below 1, the way
:class:`~grimmcraft_core.item.core_item.SlotContainer` rejects a capacity below
1: a bar with no maximum has no meaning to clamp against.

# Not yet a command

``grimmcraft-control`` has no ``bossbar`` command, so nothing here compiles to a
datapack yet. This is the domain model; adding ``CommandName.BOSSBAR`` and its
constructors is a separate change to the shared vocabulary, like ``place`` was.
"""

# Includes
from __future__ import annotations

# Includes standard
from grimmclub_standardlib import TYPE_CHECKING, UUID, Enum, Iterator, dataclass, field

# Includes internal
from grimmcraft_core.text import Text, as_text

if TYPE_CHECKING:
    from grimmcraft_core.entity.core_entity import CoreEntity

# Constants
#: How many segments a bar is drawn with in :meth:`BossBar.hud`.
HUD_SEGMENTS = 10

#: The character for a filled and an empty segment.
FILLED_SEGMENT = "▰"
EMPTY_SEGMENT = "▱"


# Types
class BossBarColor(Enum):
    """The seven colours a boss bar may be. Minecraft allows no others."""

    PINK = "pink"
    BLUE = "blue"
    RED = "red"
    GREEN = "green"
    YELLOW = "yellow"
    PURPLE = "purple"
    WHITE = "white"


class BossBarStyle(Enum):
    """Solid, or divided into notches.

    The notch counts are fixed by the game: 6, 10, 12 or 20, and nothing else.
    """

    PROGRESS = "progress"
    NOTCHED_6 = "notched_6"
    NOTCHED_10 = "notched_10"
    NOTCHED_12 = "notched_12"
    NOTCHED_20 = "notched_20"

    @property
    def notches(self) -> int | None:
        """How many segments this style shows, or ``None`` when it is solid."""
        return None if self is BossBarStyle.PROGRESS else int(self.value.split("_")[1])


# Main Class
@dataclass
class BossBar:
    """One boss bar: a name, a value out of a maximum, and an audience.

    ``bar_id`` is a namespaced id (``"village:harvest"``), which is how the game
    addresses a bar and how :class:`BossBarSet` keys them.
    """

    bar_id: str
    name: Text | str = ""
    value: int = 0
    max_value: int = 100
    color: BossBarColor = BossBarColor.WHITE
    style: BossBarStyle = BossBarStyle.PROGRESS
    visible: bool = True
    viewers: list[UUID] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.max_value < 1:
            raise ValueError(f"max_value must be at least 1, got {self.max_value}")
        self.name = as_text(self.name)
        self.value = self._clamped(self.value)

    def _clamped(self, value: int) -> int:
        return max(0, min(value, self.max_value))

    # --- the value -----------------------------------------------------------
    @property
    def progress(self) -> float:
        """How full the bar is, from ``0.0`` to ``1.0``."""
        return self.value / self.max_value

    @property
    def percent(self) -> int:
        """How full the bar is, rounded to whole percent."""
        return round(self.progress * 100)

    @property
    def is_empty(self) -> bool:
        return self.value == 0

    @property
    def is_full(self) -> bool:
        return self.value == self.max_value

    def set_value(self, value: int) -> BossBar:
        """Set the value, clamped into range. Returns ``self`` so calls chain."""
        self.value = self._clamped(value)
        return self

    def add(self, delta: int) -> BossBar:
        """Move the value by ``delta``, clamped. Negative counts down."""
        return self.set_value(self.value + delta)

    def set_max(self, max_value: int) -> BossBar:
        """Change the maximum, re-clamping the current value against it."""
        if max_value < 1:
            raise ValueError(f"max_value must be at least 1, got {max_value}")
        self.max_value = max_value
        self.value = self._clamped(self.value)
        return self

    # --- the audience --------------------------------------------------------
    @staticmethod
    def _key(viewer: CoreEntity | UUID) -> UUID:
        return viewer if isinstance(viewer, UUID) else viewer.uuid

    def show_to(self, viewer: CoreEntity | UUID) -> BossBar:
        """Add a viewer. Adding one twice does not show the bar twice."""
        key = self._key(viewer)
        if key not in self.viewers:
            self.viewers.append(key)
        return self

    def hide_from(self, viewer: CoreEntity | UUID) -> BossBar:
        """Remove a viewer (no-op if they were never shown it)."""
        key = self._key(viewer)
        if key in self.viewers:
            self.viewers.remove(key)
        return self

    def is_shown_to(self, viewer: CoreEntity | UUID) -> bool:
        """Whether ``viewer`` sees this bar — both listed *and* visible."""
        return self.visible and self._key(viewer) in self.viewers

    # --- display -------------------------------------------------------------
    def hud(self) -> str:
        """A HUD segment: ``▰▰▰▱▱▱▱▱▱▱ Harvest 30%``, or empty when hidden.

        Returning an empty string when hidden is what lets a bar sit permanently
        in a :class:`~grimmcraft_core.hud.Hud`: an empty segment is dropped, so
        no stray separator appears while the bar is off.
        """
        if not self.visible:
            return ""
        filled = round(self.progress * HUD_SEGMENTS)
        bar = FILLED_SEGMENT * filled + EMPTY_SEGMENT * (HUD_SEGMENTS - filled)
        label = str(self.name)
        return f"{bar} {label} {self.percent}%" if label else f"{bar} {self.percent}%"

    def __str__(self) -> str:
        return self.hud()


# Classes
class BossBarSet:
    """The world's boss bars, addressed by their namespaced ids.

    Mirrors how the game holds them: ``bossbar add``, ``remove``, ``list``. A
    bar has to be created before it can be set, so unlike the ender registry
    this one does **not** create on access — asking for a bar that was never
    added is a mistake worth hearing about.
    """

    def __init__(self) -> None:
        self._bars: dict[str, BossBar] = {}

    def add(self, bar: BossBar) -> BossBar:
        """Register ``bar``. Adding the same id twice is an error, as in game."""
        if bar.bar_id in self._bars:
            raise ValueError(f"a boss bar with id {bar.bar_id!r} already exists")
        self._bars[bar.bar_id] = bar
        return bar

    def create(self, bar_id: str, name: Text | str = "", **options: object) -> BossBar:
        """Build a bar and register it in one step."""
        return self.add(BossBar(bar_id=bar_id, name=name, **options))  # type: ignore[arg-type]

    def get(self, bar_id: str) -> BossBar:
        """The bar with this id, or :class:`KeyError` naming what was missing."""
        if bar_id not in self._bars:
            raise KeyError(f"no boss bar with id {bar_id!r}")
        return self._bars[bar_id]

    def remove(self, bar_id: str) -> None:
        """Delete a bar (no-op if it was never added)."""
        self._bars.pop(bar_id, None)

    def has(self, bar_id: str) -> bool:
        return bar_id in self._bars

    @property
    def ids(self) -> list[str]:
        """Every registered id, in the order they were added."""
        return list(self._bars)

    def shown_to(self, viewer: CoreEntity | UUID) -> list[BossBar]:
        """Every bar ``viewer`` currently sees, in registration order."""
        return [bar for bar in self._bars.values() if bar.is_shown_to(viewer)]

    def clear(self) -> None:
        """Forget every bar."""
        self._bars.clear()

    def __len__(self) -> int:
        return len(self._bars)

    def __iter__(self) -> Iterator[BossBar]:
        return iter(self._bars.values())
