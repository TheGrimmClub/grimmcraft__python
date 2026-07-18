# Changelog

Grouped by conventional-commit type. Newest work first.

## fix(env): make editable workspace imports survive iCloud sync

The repo lives under an iCloud-synced `~/Desktop`; iCloud sets the macOS
`UF_HIDDEN` flag on uv's editable `.pth` files, and CPython's `site.py` silently
skips hidden `.pth` files — so no `grimmcraft_*` package was importable at runtime
despite a successful `uv sync`.

- `Taskfile.yml` — `install` now runs `uv sync` then `fix-venv`
  (`chflags nohidden …/*.pth`); added the `fix-venv` task; set root
  `env: UV_NO_SYNC: "1"` so `uv run` doesn't re-hide via implicit sync; `test`
  now `deps: [fix-venv]`.
- Memory `uv-stale-pth-reinstall.md` corrected with the real root cause
  (was previously mis-attributed to stale `.pth`, "fixed" with `--reinstall`).
- ⚠️ Durable fix still recommended: move the project/venv off iCloud
  (`UV_PROJECT_ENVIRONMENT`).

## feat(redstone): model Minecraft redstone as a simulatable component graph

New package `grimmcraft-redstone` (depends on `grimmcraft-core` +
`grimmcraft-data`), under `packages/grimmcraft-redstone/srcs/grimmcraft_redstone/`.

### Core model
- `signal.py` — `Signal` (power `0-15` + `PowerKind` strong/weak/none),
  `PowerLevel`, `attenuate()`, redstone-tick timing (`redstone_ticks`).
- `component.py` — `RedstoneComponent` base; `SignalChange`; `SimContext`;
  role protocols `PowerSource` / `Conductor` / `Load` / `LogicGate`.
- `circuit.py` — `Circuit`, the spatial graph keyed by `BlockPos`.
- `simulation.py` — `Simulator` (deterministic synchronous tick engine),
  `run_until_stable()` with oscillation detection, `StepResult` /
  `StabilizeResult`, `dust_field()`.
- `diagnostics.py` — `analyze()`, `Diagnostic`, `DiagnosticBag`, `Codes`
  (stable `RS####` codes with location + fix hint).

### Four component families
- `inputs/` — `Lever`, `Button`, `RedstoneBlock`, `Observer`, `PressurePlate`,
  `WeightedPressurePlate`, `DaylightSensor`, `AnalogSource`.
- `connectors/` — `RedstoneDust` (attenuation, 15-block range), `SolidBlock`.
- `outputs/` — `RedstoneLamp`, `Piston` / `StickyPiston` (push limit, sticky
  retract, Java-only `quasi_connectivity` flag), `Dispenser`, `Dropper`,
  `NoteBlock`, `Bell`, `Hopper` (locked-while-powered), `Door` / `Trapdoor` /
  `FenceGate`, `Tnt`, `PoweredRail` / `ActivatorRail`.
- `functions/` — `RedstoneTorch` (inverter, 1 rt delay, burnout), `Repeater`
  (1-4 rt delay, diode, side-lock), `Comparator` + `Container` (compare/subtract,
  container reading), `NotGate` / `AndGate` / `OrGate` / `NandGate` / `XorGate`,
  `Clock`.

## test(redstone): behaviour-driven suite (58 tests)

`packages/grimmcraft-redstone/tests/` — dust attenuation, gate truth tables
through the simulator, repeater delay timing + lock, comparator compare/subtract
+ container, torch inversion + burnout, oscillation detection, piston
extend/retract, diagnostics.

## docs(redstone): overview, reference, gallery, diagnostics

`packages/grimmcraft-redstone/docs/` — signal model, four families, the
update-order contract, Java/Bedrock quasi-connectivity, full component table,
example gallery, and the diagnostics catalogue. Plus `README.md` and four
runnable `examples/` (lever→lamp, clock, half-adder, T-flip-flop).

## refactor(monorepo): standardise packages on `srcs/` + uv_build

- Moved `grimmcraft-control` and `grimmcraft-redstone` from `src/` to `srcs/`;
  all packages now use `uv_build` with `module-root = "srcs"`.
- `fix(cli)`: corrected `packages = ["srcs/grimmcraftcraft_cli"]` typo and the
  stale `grimm_cli.main` script → `grimmcraft = "grimmcraft_cli.main:main"`.
- `fix(tasks)`: root `data` include pointed at `Taskfile.yml` but the file is
  `Taskfile.yaml`; repaired the `new-package` scaffold command; `test` now
  auto-discovers `packages/*/tests`.
- `feat(tasks)`: added the `redstone:` include to the root `Taskfile.yml`.

## chore(pytest): enable importlib import mode

`pyproject.toml` — `addopts = "-ra --import-mode=importlib"` so sibling packages
can share test-file basenames (e.g. multiple `tests/test_diagnostics.py`) without
collisions.

## build(redstone): package manifest

`packages/grimmcraft-redstone/pyproject.toml` — description, `grimmcraft-core` +
`grimmcraft-data` workspace deps, `uv_build` backend with `srcs` module root.
