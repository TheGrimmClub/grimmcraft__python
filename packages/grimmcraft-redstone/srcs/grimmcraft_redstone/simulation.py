"""The tick-based :class:`Simulator` that brings a :class:`Circuit` to life.

**Update-order contract (deterministic).**  Each :meth:`Simulator.step` advances
the world by **one game tick** and is *synchronous*: it first snapshots every
component's published output and resolves the redstone-dust power field from that
snapshot, then evaluates every component against that frozen snapshot.  Because no
component observes another's *new* output within the same tick, the result is
independent of evaluation order; where an order is still needed (reporting,
tie-breaks) components are visited in ascending ``(x, y, z)`` position order.
Signals therefore propagate one component-hop per tick — instantaneous in
Minecraft only for dust, which is resolved globally each tick.

Delays are honoured by the components themselves (a repeater buffers its input
for ``2 x delay`` game ticks; a torch reacts after one redstone tick), and the
engine detects **oscillation**: :meth:`run_until_stable` stops as soon as the full
world state repeats and reports it, rather than looping forever on a clock.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from grimmcraft_core.coordinates import BlockPos, Direction
from grimmcraft_redstone.circuit import Circuit
from grimmcraft_redstone.component import RedstoneComponent, SignalChange
from grimmcraft_redstone.signal import OFF, Signal


@dataclass(frozen=True, slots=True)
class StepResult:
    """What happened during a single :meth:`Simulator.step`."""

    tick: int
    changes: tuple[SignalChange, ...]

    @property
    def quiet(self) -> bool:
        """True when no component's output changed this tick."""
        return not self.changes


@dataclass(slots=True)
class StabilizeResult:
    """The outcome of :meth:`Simulator.run_until_stable`."""

    ticks: int
    stable: bool
    oscillating: bool = False
    #: For an oscillating circuit, the length of the repeating cycle in ticks.
    period: int | None = None

    def __bool__(self) -> bool:
        return self.stable


class _Snapshot:
    """A frozen, read-only :class:`SimContext` for one tick.

    Holds the pre-update outputs and the resolved dust field so every component
    evaluates against the same consistent world, making a tick order-independent.
    """

    __slots__ = ("_circuit", "_outputs", "_dust", "tick")

    def __init__(
        self,
        circuit: Circuit,
        outputs: dict[BlockPos, Signal],
        dust: dict[BlockPos, int],
        tick: int,
    ) -> None:
        self._circuit = circuit
        self._outputs = outputs
        self._dust = dust
        self.tick = tick

    def output_at(self, pos: BlockPos) -> Signal:
        return self._outputs.get(pos, OFF)

    def component_at(self, pos: BlockPos) -> RedstoneComponent | None:
        return self._circuit.get(pos)

    def dust_power(self, pos: BlockPos) -> int:
        return self._dust.get(pos, 0)

    def power_into(self, pos: BlockPos, direction: Direction) -> Signal:
        """The signal reaching ``pos`` from its neighbour toward ``direction``."""
        npos = pos.step(direction)
        neighbor = self._circuit.get(npos)
        if neighbor is None:
            # An empty cell may still be a solid block re-emitting strong power.
            strong = self._block_strong_power(npos)
            return Signal.strong(strong) if strong else OFF
        if neighbor.IS_DUST:
            level = self._dust.get(npos, 0)
            return Signal.weak(level) if level else OFF
        if neighbor.IS_SOLID:
            strong = self._block_strong_power(npos)
            return Signal.strong(strong) if strong else OFF
        if neighbor.EMITS_POWER:
            return self._outputs.get(npos, OFF)
        return OFF

    def incoming_power(self, component: RedstoneComponent) -> Signal:
        """The strongest signal on any of ``component``'s input faces."""
        best = OFF
        for direction in component.inputs():
            best = max(best, self.power_into(component.position, direction))
        return best

    def block_powered(self, pos: BlockPos) -> bool:
        """Whether the solid block at ``pos`` is powered (strong or weak)."""
        if self._block_strong_power(pos):
            return True
        for direction in Direction:
            npos = pos.step(direction)
            neighbor = self._circuit.get(npos)
            if neighbor is None:
                continue
            if neighbor.IS_DUST and self._dust.get(npos, 0) > 0:
                return True
        return False

    def _block_strong_power(self, pos: BlockPos) -> int:
        """Strong power level a solid block at ``pos`` receives from neighbours."""
        if not self._circuit.is_solid(pos):
            return 0
        best = 0
        for direction in Direction:
            neighbor = self._circuit.get(pos.step(direction))
            if neighbor is None or not neighbor.EMITS_POWER:
                continue
            # A redstone torch never powers the block it is mounted on — that is
            # exactly why a floor torch is stable rather than a clock.
            if getattr(neighbor, "attachment_pos", None) == pos:
                continue
            sig = self._outputs.get(neighbor.position, OFF)
            if sig.is_strong:
                best = max(best, sig.level)
        return best


@dataclass(slots=True)
class Simulator:
    """Drives a :class:`Circuit` forward in discrete game ticks."""

    circuit: Circuit
    tick: int = 0
    components_ever_powered: set[BlockPos] = field(default_factory=set)

    # -- stepping -------------------------------------------------------------
    def step(self) -> StepResult:
        """Advance the world by one game tick and return the resulting changes."""
        self.tick += 1
        outputs = {pos: comp.output_signal() for pos, comp in self.circuit.items()}
        dust = self._resolve_dust(outputs)
        ctx = _Snapshot(self.circuit, outputs, dust, self.tick)

        changes: list[SignalChange] = []
        for _pos, component in self.circuit.items():
            changes.extend(component.update(ctx, self.tick))

        for pos, component in self.circuit.items():
            if (
                component.output_signal().is_on
                or ctx.incoming_power(component).is_on
                or (component.IS_DUST and dust.get(pos, 0) > 0)
            ):
                self.components_ever_powered.add(pos)

        return StepResult(self.tick, tuple(changes))

    def run_until_stable(self, max_ticks: int = 200) -> StabilizeResult:
        """Step until the world stops changing, or declare it oscillating.

        Returns as soon as a tick reproduces the previous full state (a fixpoint)
        or a *previously seen* state recurs (a cycle → a clock).  Never loops
        longer than ``max_ticks``.
        """
        seen: dict[tuple[object, ...], int] = {}
        previous = self._signature()
        seen[previous] = 0
        for _ in range(max_ticks):
            self.step()
            signature = self._signature()
            if signature == previous:
                return StabilizeResult(self.tick, stable=True)
            if signature in seen:
                return StabilizeResult(
                    self.tick,
                    stable=False,
                    oscillating=True,
                    period=len(seen) - seen[signature],
                )
            seen[signature] = len(seen)
            previous = signature
        return StabilizeResult(self.tick, stable=False, oscillating=True)

    def run(self, ticks: int) -> list[StepResult]:
        """Step exactly ``ticks`` times, returning each :class:`StepResult`."""
        return [self.step() for _ in range(ticks)]

    # -- dust field -----------------------------------------------------------
    def _resolve_dust(self, outputs: dict[BlockPos, Signal]) -> dict[BlockPos, int]:
        """Resolve the redstone-wire power field by attenuating from every source.

        Each dust cell is first seeded from any adjacent emitter (or strongly
        powered solid block), then relaxed so power spreads through connected dust
        losing one level per block — giving dust its characteristic 15-block range.
        """
        dust_cells = [p for p, c in self.circuit.items() if c.IS_DUST]
        power: dict[BlockPos, int] = {}
        for pos in dust_cells:
            best = 0
            for direction in Direction:
                npos = pos.step(direction)
                neighbor = self.circuit.get(npos)
                if neighbor is not None and neighbor.EMITS_POWER:
                    sig = outputs.get(npos, OFF)
                    if sig.is_on:
                        best = max(best, sig.level)
                elif self.circuit.is_solid(npos):
                    strong = _Snapshot(
                        self.circuit, outputs, {}, self.tick
                    )._block_strong_power(npos)
                    best = max(best, strong)
            power[pos] = best

        # Relaxation: repeatedly pull (neighbour_dust - 1) until it settles.
        changed = True
        while changed:
            changed = False
            for pos in dust_cells:
                for direction in Direction:
                    npos = pos.step(direction)
                    if npos in power:
                        candidate = power[npos] - 1
                        if candidate > power[pos]:
                            power[pos] = candidate
                            changed = True
        return power

    # -- oscillation signature ------------------------------------------------
    def _signature(self) -> tuple[object, ...]:
        """A hashable snapshot of the whole circuit's runtime state."""
        return tuple(
            (pos.x, pos.y, pos.z, comp.state_key()) for pos, comp in self.circuit.items()
        )


def dust_field(circuit: Circuit) -> dict[BlockPos, int]:
    """Convenience: resolve the dust power field for ``circuit``'s current state."""
    sim = Simulator(circuit)
    outputs = {pos: comp.output_signal() for pos, comp in circuit.items()}
    return sim._resolve_dust(outputs)


__all__ = [
    "Simulator",
    "StepResult",
    "StabilizeResult",
    "dust_field",
]
