# grimmcraft-redstone

A simulatable model of Minecraft redstone as a **component graph**. Place
components in a `Circuit`, drive it with a tick-based `Simulator`, and read the
signals back.

```python
from grimmcraft_core.coordinates import BlockPos
from grimmcraft_redstone import Circuit, Lever, RedstoneDust, RedstoneLamp, Simulator

circuit = Circuit()
lever = circuit.place(Lever(BlockPos(0, 0, 0), on=True))
circuit.place(RedstoneDust(BlockPos(1, 0, 0)))
lamp = circuit.place(RedstoneLamp(BlockPos(2, 0, 0)))

Simulator(circuit).run_until_stable()
assert lamp.lit
```

## Components (four families)

- **inputs** — `Lever`, `Button`, `RedstoneBlock`, `Observer`, `PressurePlate`,
  `WeightedPressurePlate`, `DaylightSensor`, `AnalogSource`
- **connectors** — `RedstoneDust`, `SolidBlock`
- **outputs** — `RedstoneLamp`, `Piston`/`StickyPiston`, `Dispenser`, `Dropper`,
  `NoteBlock`, `Bell`, `Hopper`, `Door`/`Trapdoor`/`FenceGate`, `Tnt`, rails
- **functions** — `RedstoneTorch` (NOT), `Repeater`, `Comparator`, `Container`,
  `NotGate`/`AndGate`/`OrGate`/`NandGate`/`XorGate`, `Clock`

## The signal model

A `Signal` is a power level `0..15` plus a `PowerKind` (strong/weak/none). Dust
loses one level per block (15-block range); a redstone tick is 2 game ticks.

## Docs & examples

- [`docs/overview.md`](docs/overview.md) — signal model, families, the
  update-order contract, Java/Bedrock quasi-connectivity
- [`docs/components.md`](docs/components.md) — full component reference table
- [`docs/gallery.md`](docs/gallery.md) — the example circuits
- [`docs/diagnostics.md`](docs/diagnostics.md) — `analyze()` and the `RS####` codes
- [`examples/`](examples) — runnable circuits (lever→lamp, clock, half-adder,
  T-flip-flop)

## Tasks

```
task redstone:test               # run the test suite
task redstone:example -- clock   # run an example
task redstone:lint
task redstone:typecheck
```

Reuses `grimmcraft-core` (`Coordinates`/`BlockPos`/`Direction`) and
`grimmcraft-data` (`Block`).
