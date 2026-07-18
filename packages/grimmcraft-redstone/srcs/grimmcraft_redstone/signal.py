"""The redstone signal value objects and the tick timing model.

A redstone :class:`Signal` carries a :class:`PowerLevel` (an integer **0-15**)
and a :class:`PowerKind` (how it powers a neighbouring solid block).  Everything
here is a pure, immutable, hashable value object — the simulation engine in
:mod:`grimmcraft_redstone.simulation` does all the mutation.

Timing note: a **redstone tick is two game ticks** (0.1 s at 20 tps).  Repeater
and comparator delays are quoted in *redstone* ticks; button pulse durations and
the observer pulse are quoted in *game* ticks.  Use :data:`GAME_TICKS_PER_SECOND`
and :func:`redstone_ticks` / :func:`game_ticks` to convert so the engine's clock
(which counts game ticks) stays correct.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum

#: The maximum signal strength a redstone source emits.
MAX_POWER = 15

#: The minimum (fully off) signal strength.
MIN_POWER = 0

#: Redstone dust carries 15 blocks before it hits zero: one lost per block.
DUST_RANGE = MAX_POWER

#: Base clock rate of a Minecraft world.
GAME_TICKS_PER_SECOND = 20

#: One redstone tick equals two game ticks (0.1 s).
GAME_TICKS_PER_REDSTONE_TICK = 2

#: A ``PowerLevel`` is conceptually an int in ``0..15``.  The alias documents
#: intent; use :class:`Signal` or the helpers below to keep it clamped.
type PowerLevel = int


def clamp_power(level: int) -> PowerLevel:
    """Clamp an arbitrary integer into the valid ``0..15`` power range."""
    if level < MIN_POWER:
        return MIN_POWER
    if level > MAX_POWER:
        return MAX_POWER
    return level


def redstone_ticks(n: int) -> int:
    """Convert ``n`` redstone ticks to game ticks (the engine's base unit)."""
    return n * GAME_TICKS_PER_REDSTONE_TICK


def game_ticks(n: int) -> int:
    """Identity helper documenting that ``n`` is already in game ticks."""
    return n


class PowerKind(IntEnum):
    """How a signal powers the block it flows into.

    Minecraft distinguishes *strong* and *weak* power.  A component (redstone
    block, a repeater/comparator output, a torch) **strongly** powers a solid
    block, which then re-emits power to everything adjacent to it.  Redstone dust
    and most passive sources only **weakly** power a block, which powers directly
    wired components but is not re-emitted through the block.  :attr:`NONE` is the
    absence of power.

    Ordered ``NONE < WEAK < STRONG`` so that the strongest of several signals
    wins a tie in :func:`max` on equal power levels.
    """

    NONE = 0
    WEAK = 1
    STRONG = 2

    @property
    def label(self) -> str:
        """The lower-case name (``"none"`` / ``"weak"`` / ``"strong"``)."""
        return self.name.lower()


@dataclass(frozen=True, slots=True, order=True)
class Signal:
    """An emitted redstone signal: a :class:`PowerLevel` plus its :class:`PowerKind`.

    Ordering/equality are by ``(level, kind)`` so signals can be compared and the
    strongest of several taken with :func:`max`.  A ``level`` of 0 is always
    :attr:`PowerKind.NONE`.
    """

    level: PowerLevel = MIN_POWER
    kind: PowerKind = PowerKind.NONE

    def __post_init__(self) -> None:
        clamped = clamp_power(self.level)
        kind = PowerKind.NONE if clamped == MIN_POWER else self.kind
        # frozen dataclass: bypass the immutability guard to normalise.
        object.__setattr__(self, "level", clamped)
        object.__setattr__(self, "kind", kind)

    # -- constructors ---------------------------------------------------------
    @classmethod
    def off(cls) -> Signal:
        """A fully unpowered signal."""
        return cls(MIN_POWER, PowerKind.NONE)

    @classmethod
    def strong(cls, level: PowerLevel = MAX_POWER) -> Signal:
        """A strongly-powering signal at ``level`` (default full strength)."""
        return cls(level, PowerKind.STRONG)

    @classmethod
    def weak(cls, level: PowerLevel = MAX_POWER) -> Signal:
        """A weakly-powering signal at ``level`` (default full strength)."""
        return cls(level, PowerKind.WEAK)

    # -- queries --------------------------------------------------------------
    @property
    def is_on(self) -> bool:
        """True when this signal carries any power at all."""
        return self.level > MIN_POWER

    @property
    def is_strong(self) -> bool:
        """True when this signal strongly powers a solid block."""
        return self.kind is PowerKind.STRONG and self.is_on

    # -- transforms -----------------------------------------------------------
    def attenuate(self, blocks: int = 1) -> Signal:
        """Return this signal weakened by ``blocks`` (redstone dust loses 1/block).

        The result is always :attr:`PowerKind.WEAK` — attenuation only happens as
        power travels through dust, which powers weakly.
        """
        return Signal(clamp_power(self.level - blocks), PowerKind.WEAK)

    def as_weak(self) -> Signal:
        """This signal downgraded to weak power (same level)."""
        return Signal(self.level, PowerKind.WEAK if self.is_on else PowerKind.NONE)

    def with_level(self, level: PowerLevel) -> Signal:
        """This signal at a different ``level``, keeping its :class:`PowerKind`."""
        return Signal(level, self.kind)

    def __bool__(self) -> bool:
        return self.is_on

    def __str__(self) -> str:
        return f"{self.level}({self.kind.label})"


#: A shared, interned "off" signal for the common no-power case.
OFF = Signal.off()
