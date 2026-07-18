# Changelog — grimmcraft-redstone

## feat(redstone): model Minecraft redstone as a simulatable component graph

New package (depends on `grimmcraft-core` + `grimmcraft-data`), under `srcs/grimmcraft_redstone/`.

### Core model
- `signal.py` — `Signal` (power `0-15` + `PowerKind` strong/weak/none), `PowerLevel`, `attenuate()`, redstone-tick timing (`redstone_ticks`).
- `component.py` — `RedstoneComponent` base; `SignalChange`; `SimContext`; role protocols `PowerSource` / `Conductor` / `Load` / `LogicGate`.
- `circuit.py` — `Circuit`, the spatial graph keyed by `BlockPos`.
- `simulation.py` — `Simulator` (deterministic synchronous tick engine), `run_until_stable()` with oscillation detection, `StepResult` / `StabilizeResult`, `dust_field()`.
- `diagnostics.py` — `analyze()`, `Diagnostic`, `DiagnosticBag`, `Codes` (stable `RS####` codes with location + fix hint).

### Four component families
- `inputs/` — `Lever`, `Button`, `RedstoneBlock`, `Observer`, `PressurePlate`, `WeightedPressurePlate`, `DaylightSensor`, `AnalogSource`.
- `connectors/` — `RedstoneDust` (attenuation, 15-block range), `SolidBlock`.
- `outputs/` — `RedstoneLamp`, `Piston` / `StickyPiston` (push limit, sticky retract, Java-only `quasi_connectivity` flag), `Dispenser`, `Dropper`, `NoteBlock`, `Bell`, `Hopper` (locked-while-powered), `Door` / `Trapdoor` / `FenceGate`, `Tnt`, `PoweredRail` / `ActivatorRail`.
- `functions/` — `RedstoneTorch` (inverter, 1 rt delay, burnout), `Repeater` (1-4 rt delay, diode, side-lock), `Comparator` + `Container` (compare/subtract, container reading), `NotGate` / `AndGate` / `OrGate` / `NandGate` / `XorGate`, `Clock`.

## test(redstone): behaviour-driven suite (58 tests)

`tests/` — dust attenuation, gate truth tables through the simulator, repeater delay timing + lock, comparator compare/subtract + container, torch inversion + burnout, oscillation detection, piston extend/retract, diagnostics.

## docs(redstone): overview, reference, gallery, diagnostics

`docs/` — signal model, four families, the update-order contract, Java/Bedrock quasi-connectivity, full component table, example gallery, and the diagnostics catalogue. Plus `README.md` and four runnable `examples/` (lever→lamp, clock, half-adder, T-flip-flop).

## build(redstone): package manifest

`pyproject.toml` — description, `grimmcraft-core` + `grimmcraft-data` workspace deps, `uv_build` backend with `srcs` module root.
