# Architecture

The compiler is a **backend for `grimmcraft-control` state machines**. A machine
is the single source of behaviour; the compiler lowers its declarative structure
to an installable Minecraft datapack. Nothing about behaviour is invented here.

## Pipeline

```
collect → build IR → validate → render (dialect) → emit tree → verify
```

| Stage | Module | What it does |
|-------|--------|--------------|
| collect | (caller) | Gather the `Machine`s to compile. |
| build IR | `lower.py` | Machines → a dialect-independent `Datapack` IR. |
| validate | `validate.py`, `registry.py` | Check ids against `grimmcraft-data`, refs, locations, portability. |
| render | `dialect.py` | Turn each IR `Command` into version-correct text. |
| emit | `emit.py` | Write `pack.mcmeta`, folders, functions, tags, `INSTALL.md`. |
| verify | `verify.py` | Re-read the tree and confirm it will load. |

`compiler.py` orchestrates the stages and returns a `CompileResult`
(the IR, a `DiagnosticBag`, and the output path).

## The IR (dialect-independent)

`ir.py` describes a datapack without any command *text*:

- `Function` — a `ResourceLocation` id + an ordered list of declarative
  `Command`s (reused from `grimmcraft_control.machine`).
- `FunctionTag` — `minecraft:load` / `minecraft:tick` (and custom tags).
- `Resource` — arbitrary JSON (loot tables, recipes, …), tagged with a singular
  `category` the emitter pluralises for old versions.
- `Datapack` — the aggregate, plus `namespace` and `description`.

Because the IR holds *commands as data*, the same IR renders correctly for any
target version.

## Lowering a machine

For a machine named `door`:

- **states → a scoreboard value.** Each state gets an integer index; the current
  index lives under the `grimmcraft_state` objective, keyed by the machine name.
- **init** (`door/init`) sets the initial state score and runs the initial
  state's enter commands. Called from the pack's `load` function.
- **events → trigger functions.** `door/on_open` runs, for each transition on
  `open`, an `execute if score … run function door/do_…` guarded by the source
  state (and a declarative `Condition` if present).
- **transitions → guarded sequences.** `door/do_closed__open__open` runs
  `on_exit` → the transition's commands → the state write → `on_enter`.
- **cycle + automatic transitions → the tick function.** A state's per-tick
  `cycle` commands run first in `door/tick_<state>`, then its automatic (`"tick"`
  event) transitions are checked — so an auto transition is always evaluated
  *after* the state's cycle commands. The machine's `tick` dispatches to the
  current state's `tick_<state>`, and is registered in `minecraft:tick`.

## The dialect (the one place version syntax lives)

`dialect.py` renders each `Command`. Everything version-specific is resolved from
the `Target`:

- **item/block data:** components (`item[minecraft:custom_name=…]`) on 1.20.5+,
  NBT tags (`item{display:{Name:'…'}}`) before.
- **text components:** SNBT (`{text:"…"}`) on 1.21.5+, JSON (`{"text":"…"}`)
  before.
- **folder scheme** (`emit.py`): singular `function/` on 1.21+, plural
  `functions/` before.

Add a version by adding a row to `version.py`'s `SUPPORT_TABLE`; add a command by
adding an `_r_<name>` method to the `Dialect`.
