"""Concrete power sources — the *inputs* family.

Every source yields a :class:`~grimmcraft_redstone.signal.Signal`.  Toggles
(lever) hold; momentary sources (button, observer) emit a timed pulse whose
length is in *game* ticks; analog sources (weighted plate, daylight sensor,
lectern, target) emit a settable 0-15 level.
"""

from __future__ import annotations

from collections.abc import Sequence

from grimmcraft_core.coordinates import BlockPos, Direction
from grimmcraft_data.block import Block
from grimmcraft_redstone.component import SignalChange, SimContext
from grimmcraft_redstone.inputs.base import Source
from grimmcraft_redstone.signal import MAX_POWER, OFF, Signal, clamp_power


class Lever(Source):
    """A toggle: emits full strong power while flipped on."""

    BLOCK = Block.LEVER

    def __init__(
        self, position: BlockPos, *, facing: Direction = Direction.UP, on: bool = False
    ) -> None:
        super().__init__(position, facing=facing)
        self.on = on
        self._refresh()

    def _desired_output(self) -> Signal:
        return Signal.strong() if self.on else OFF

    def toggle(self) -> Lever:
        """Flip the lever and republish; returns self for chaining."""
        self.on = not self.on
        self._refresh()
        return self

    def set(self, on: bool) -> Lever:
        """Set the lever on/off and republish."""
        self.on = on
        self._refresh()
        return self

    def state_key(self) -> tuple[object, ...]:
        return (*super().state_key(), self.on)


#: Button pulse length by material, in *game* ticks (wood 30, stone 20).
_BUTTON_TICKS = {"wooden": 30, "stone": 20}


class Button(Source):
    """A momentary push button: a timed strong pulse, then off.

    ``material`` picks the pulse length — ``"wooden"`` (1.5 s / 30 gt) or
    ``"stone"`` (1.0 s / 20 gt).
    """

    BLOCK = Block.STONE_BUTTON

    def __init__(
        self,
        position: BlockPos,
        *,
        facing: Direction = Direction.UP,
        material: str = "stone",
    ) -> None:
        block = Block.OAK_BUTTON if material == "wooden" else Block.STONE_BUTTON
        super().__init__(position, facing=facing, block_type=block)
        self.material = material
        self.duration = _BUTTON_TICKS[material]
        self._remaining = 0

    def press(self) -> Button:
        """Push the button, starting its pulse."""
        self._remaining = self.duration
        self._refresh()
        return self

    def _desired_output(self) -> Signal:
        return Signal.strong() if self._remaining > 0 else OFF

    def update(self, ctx: SimContext, tick: int) -> Sequence[SignalChange]:
        if self._remaining > 0:
            self._remaining -= 1
        return self._set_output(self._desired_output())

    @property
    def pressed(self) -> bool:
        """Whether the button is currently held down (mid-pulse)."""
        return self._remaining > 0

    def state_key(self) -> tuple[object, ...]:
        return (*super().state_key(), self._remaining)


class RedstoneBlock(Source):
    """A block of redstone: a constant full-strength source."""

    BLOCK = Block.REDSTONE_BLOCK

    def __init__(self, position: BlockPos) -> None:
        super().__init__(position)
        self._output = Signal.strong()

    def _desired_output(self) -> Signal:
        return Signal.strong()


class PressurePlate(Source):
    """A plate that emits full power while something stands on it (boolean)."""

    BLOCK = Block.STONE_PRESSURE_PLATE

    def __init__(
        self, position: BlockPos, *, block_type: Block = Block.STONE_PRESSURE_PLATE
    ) -> None:
        super().__init__(position, block_type=block_type)
        self.entities = 0

    def set_entities(self, count: int) -> PressurePlate:
        """Set how many entities are standing on the plate and republish."""
        self.entities = max(0, count)
        self._refresh()
        return self

    def _desired_output(self) -> Signal:
        return Signal.strong() if self.entities > 0 else OFF

    def state_key(self) -> tuple[object, ...]:
        return (*super().state_key(), self.entities)


class WeightedPressurePlate(PressurePlate):
    """A weighted plate whose analog output scales with the entity count.

    ``sensitivity`` is entities-per-power-level: ``light`` (gold) reaches 15 at 15
    entities; ``heavy`` (iron) reaches 15 at 150 (10 per level).
    """

    BLOCK = Block.LIGHT_WEIGHTED_PRESSURE_PLATE

    def __init__(self, position: BlockPos, *, heavy: bool = False) -> None:
        block = (
            Block.HEAVY_WEIGHTED_PRESSURE_PLATE
            if heavy
            else Block.LIGHT_WEIGHTED_PRESSURE_PLATE
        )
        super().__init__(position, block_type=block)
        self._per_level = 10 if heavy else 1

    def _desired_output(self) -> Signal:
        if self.entities <= 0:
            return OFF
        level = clamp_power((self.entities + self._per_level - 1) // self._per_level)
        return Signal.strong(level)


class DaylightSensor(Source):
    """A daylight detector: analog output from the sky light, optionally inverted."""

    BLOCK = Block.DAYLIGHT_DETECTOR

    def __init__(self, position: BlockPos, *, inverted: bool = False) -> None:
        super().__init__(position)
        self.inverted = inverted
        self.sky_light = 0

    def set_sky_light(self, level: int) -> DaylightSensor:
        """Set the current sky-light level (0-15) and republish."""
        self.sky_light = clamp_power(level)
        self._refresh()
        return self

    def _desired_output(self) -> Signal:
        level = MAX_POWER - self.sky_light if self.inverted else self.sky_light
        return Signal.strong(clamp_power(level))

    def state_key(self) -> tuple[object, ...]:
        return (*super().state_key(), self.sky_light, self.inverted)


class Observer(Source):
    """A directional block-update detector emitting a short pulse on change.

    It watches the cell in front (``facing``) and, when that cell's output signal
    changes between ticks, emits a ``pulse_ticks`` (default 2 gt = 1 redstone
    tick) strong pulse from its back face.
    """

    BLOCK = Block.OBSERVER

    def __init__(
        self,
        position: BlockPos,
        *,
        facing: Direction = Direction.NORTH,
        pulse_ticks: int = 2,
    ) -> None:
        super().__init__(position, facing=facing)
        self.pulse_ticks = pulse_ticks
        self._remaining = 0
        self._last_seen: tuple[int, int] | None = None

    @property
    def watch_pos(self) -> BlockPos:
        """The cell this observer watches (one step along ``facing``)."""
        return self.position.step(self.facing)

    def _desired_output(self) -> Signal:
        return Signal.strong() if self._remaining > 0 else OFF

    def update(self, ctx: SimContext, tick: int) -> Sequence[SignalChange]:
        observed = ctx.output_at(self.watch_pos)
        key = (observed.level, observed.kind.value)
        if self._last_seen is not None and key != self._last_seen:
            self._remaining = self.pulse_ticks
        self._last_seen = key
        if self._remaining > 0:
            self._remaining -= 1
        return self._set_output(self._desired_output())

    def state_key(self) -> tuple[object, ...]:
        return (*super().state_key(), self._remaining, self._last_seen)


class AnalogSource(Source):
    """A generic settable analog source (target block, lectern, tripwire, rails).

    Models the family members whose behaviour is "emit a level someone sets"
    (a target block's hit strength, a lectern's page, a detector rail's cart) so
    they participate in circuits without bespoke physics each.
    """

    def __init__(
        self,
        position: BlockPos,
        *,
        block_type: Block,
        strong: bool = True,
    ) -> None:
        super().__init__(position, block_type=block_type)
        self._strong = strong
        self.level = 0

    def emit(self, level: int) -> AnalogSource:
        """Set the emitted power level (0-15) and republish."""
        self.level = clamp_power(level)
        self._refresh()
        return self

    def _desired_output(self) -> Signal:
        if self.level <= 0:
            return OFF
        return Signal.strong(self.level) if self._strong else Signal.weak(self.level)

    def state_key(self) -> tuple[object, ...]:
        return (*super().state_key(), self.level)


def TargetBlock(position: BlockPos) -> AnalogSource:
    """A target block — analog output from projectile hit strength (settable)."""
    return AnalogSource(position, block_type=Block.TARGET)


def Lectern(position: BlockPos) -> AnalogSource:
    """A lectern — analog output from the open page (settable)."""
    return AnalogSource(position, block_type=Block.LECTERN)


def TripwireHook(position: BlockPos, *, facing: Direction = Direction.NORTH) -> AnalogSource:
    """A tripwire hook — boolean-ish source (set 15 when the wire is tripped)."""
    source = AnalogSource(position, block_type=Block.TRIPWIRE_HOOK)
    source.facing = facing
    return source


def DetectorRail(position: BlockPos) -> AnalogSource:
    """A detector rail — emits full power while a minecart is on it (settable)."""
    return AnalogSource(position, block_type=Block.DETECTOR_RAIL)
