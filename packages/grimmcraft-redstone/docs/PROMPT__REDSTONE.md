# Task: implement the redstone model in the grimmcraft-redstone package
> [x] run PROMPT_REDSTONE.md 

If you sugesst a task to execute show it as a taskfile like task with a description element (`desc`)

Model Minecraft redstone as a simulatable component graph. Write it in the
**`grimmcraft-redstone`** package
(`packages/grimmcraft-redstone/src/grimmcraft_redstone/`), with `tests/`,
`examples/`, and `docs/` under `packages/grimmcraft-redstone/`.
**First inspect the sibling packages** (`grimmcraft-data`, `grimmcraft-core`,
`grimmcraft-control`) and match their conventions (Python version,
dataclass/pydantic, typing, layout, lint/type config, Taskfile, docs tooling).

## Reuse the other packages

- **grimmcraft-data** — every component's `block_type` is a `Block` enum member;
  validate ids against the target where relevant.
- **grimmcraft-core** — reuse `Coordinates`/`BlockPos` for placement and
  `Direction` for facing/orientation. Components are placed in a world grid.
- **grimmcraft-control** (`machine`) — model the naturally *discrete* components
  (lever, button, repeater lock, observer pulse) as small state machines where it
  reads cleanly. Analog signal propagation (dust, comparator arithmetic) is
  handled by the simulation engine, not an FSM. Keep the coupling optional.

## Signal model (`signal.py`)

- `Signal`/`PowerLevel` — an int **0–15** value object with clamping and helpers
  (`is_on`, `attenuate(n)`). Redstone dust loses **1 per block** (range 15).
- Distinguish **strong** vs **weak** power and note that a solid block can be
  powered and re-emit to adjacent components.
- A redstone **tick = 2 game ticks (0.1 s)**; repeater/comparator delays are in
  redstone ticks. Encode this so the engine's timing is correct.

## Component taxonomy (the four families)

Base `RedstoneComponent` (position: Coordinates, facing: Direction, block_type:
Block) with an interface: `output_signal() -> Signal`, `inputs() ->
Iterable[Direction]`, `update(ctx, tick) -> list[SignalChange]`. Use small
Protocols like `PowerSource`, `Conductor`, `Load`, `LogicGate`.

- **inputs/ (sources)** — `Button` (momentary pulse: wood 30 gt / stone 20 gt),
  `Lever` (toggle), `Observer` (1-tick pulse on a watched block update,
  directional), `PressurePlate` (+ weighted variants), `RedstoneBlock` (constant
  15), `DaylightSensor` (+ inverted), `TripwireHook`, `TargetBlock`,
  `DetectorRail`, `Lectern`. Each yields a `Signal`.
- **connectors/ (transmission)** — `RedstoneDust`/wire with directional
  connections and per-block attenuation; represent how it reads from sources and
  feeds loads, and how solid blocks conduct (strong/weak). This family carries
  signal, it doesn't originate or consume it.
- **outputs/ (loads)** — `RedstoneLamp`, `Piston`/`StickyPiston` (extend/retract,
  push limit 12, sticky retract quirks), `Dispenser`, `Dropper`, `Hopper`
  (locked while powered), `NoteBlock`, `Door`/`Trapdoor`/`FenceGate`, `TNT`,
  `PoweredRail`/`ActivatorRail`, `Bell`. Each reacts to incoming power.
- **functions/ (logic)** — `RedstoneTorch` = **inverter/NOT** (off when its
  attachment block is powered; models burnout under rapid toggling),
  `Comparator` (two modes: **compare** vs **subtract**; reads container fullness
  0–15 and does signal-strength math), `Repeater` (**1–4 rt delay**,
  one-directional **diode**, side-input **lock**). Provide composite gates built
  from these primitives: `NotGate`, `AndGate`, `OrGate`, `XorGate`,
  `NandGate`, plus a simple `Clock` (torch/repeater loop).

## Circuit + simulation (`circuit.py`, `simulation.py`)

- `Circuit` — a spatial graph of placed components keyed by `BlockPos`;
  add/remove/connect; resolve neighbors by `Direction`.
- `Simulator` — a **tick-based** engine: schedule updates, propagate signals in
  a deterministic order, respect repeater/comparator delays and torch burnout,
  `step()` one tick and `run_until_stable(max_ticks)`; **detect oscillation**
  (clocks) and stop with a diagnostic rather than looping forever.
- Determinism and update ordering must be documented — redstone is
  order-sensitive; pick a defined scheme and state it.

## Accuracy notes / nuances to get right

- Dust attenuation and the 15-block range; torch inversion and burnout;
  repeater delay + diode + lock; comparator compare-vs-subtract and container
  reading; observer 1-tick pulse; button pulse durations by material.
- **Quasi-connectivity / BUD** (pistons, dispensers, droppers powered
  "through" a block one above) is **Java-only** and differs from Bedrock —
  implement it behind a flag and clearly document the Java/Bedrock difference, or
  explicitly declare it out of scope. Don't model it silently.

## Diagnostics

Reuse or mirror the project's diagnostics style (as in the compiler): warn on
floating/never-powered components, invalid orientation (e.g. comparator not
facing a readable block), likely-unintended clocks/oscillation, torch on a block
it can't attach to, and comparator reading a non-container. Messages should say
what's wrong, where (position/component), and how to fix it.

## Also generate — tests, examples, docs (in the package)

- **tests/** (pytest, `uv run pytest`, hermetic): truth tables for the logic
  gates (NOT/AND/OR/XOR/NAND) driven through the simulator; dust attenuation over
  distance; repeater delay timing; comparator subtract vs compare with a mock
  container; torch inversion + burnout; oscillation detection on a clock;
  piston extend/retract on power. Parametrize where natural.
- **examples/**: a few runnable circuits — e.g. a lever→lamp, a T-flip-flop, a
  2-tick clock, and one non-trivial gate (XOR or a 1-bit adder) — printing the
  simulated signal states per tick.
- **docs/**: overview of the signal model and the four families, the update-order
  contract, a component reference table (block, family, behavior, delay), and a
  gallery of the example circuits (with Mermaid or ASCII layout). Match the
  repositories docs tooling.

## Deliverable checklist

- `python -c "import grimmcraft_redstone"` works; public API re-exported.
- Logic-gate truth tables pass through the real simulator; timing tests match the
  redstone-tick model; oscillation is detected, not hung.
- `uv run pytest` green and hermetic; examples run; docs render.
- Type-checks clean; style consistent with the other grimmcraft packages; add
  Taskfile tasks (test, run example, build docs) matching existing style.
