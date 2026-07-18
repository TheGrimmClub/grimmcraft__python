# Task: build the grimmcraft mcfunction → Python decompiler
> [ ] TODO: execute PROMPT__DECOMPILER.md

Implement a Python **decompiler** that lifts an installed Minecraft **datapack**
back into the grimmcraft domain model — the inverse of `grimmcraft-compiler`. Put
it in a dedicated package `packages/grimmcraft-decompiler/srcs/grimmcraft_decompiler/`
and match the repository conventions (uv workspace, Python ≥3.12, `srcs/` layout,
frozen dataclasses, click + rich, ruff/mypy config, Taskfile, docs).
**First inspect the sibling packages and reuse them — do not re-implement what
they already provide.** The compiler is the source of truth for the IR, the
`Dialect`, `Target`/version table and diagnostics; the decompiler is its mirror.

## Use all available packages

- **grimmcraft-compiler** — reuse its `Datapack`/`Function`/`FunctionTag`/
  `ResourceLocation` IR, the `Target`/`VersionInfo` support table, the `Dialect`
  (as the reference for *how* a command was rendered), the command vocabulary
  (`CommandName`/`ConditionName`), and the `Diagnostic`/`DiagnosticBag` system.
  Decompiling is "run the compiler backwards", so share its types, never fork
  them.
- **grimmcraft-control** — the reconstruction target: rebuild `Machine`s (states,
  transitions, cycle commands, conditions) via `new_machine(...)`/`MachineBuilder`
  so a decompiled pack round-trips through the compiler unchanged.
- **grimmcraft-data** — validate every recovered `Block`/`Item`/`Entity` id for
  the detected version; use it for "unknown id" and rename diagnostics exactly as
  the compiler does.
- **grimmcraft-core / grimmclub** — `BlockPos`/`Coordinates` for parsed positions;
  `grimmclub` for the standard-library facade + debug logging.

## What "decompile" means (three levels, each a valid `--emit` target)

1. **IR** — parse the datapack tree into the compiler's `Datapack` IR: every
   `.mcfunction` line back into a declarative `Command`, plus tags and resources.
   This level works for **any** datapack, grimmcraft-generated or not.
2. **Machine** — recognise the grimmcraft conventions in the IR (the
   `grimmcraft_state` scoreboard, `<machine>/init`, `on_<event>`, `do_<…>`,
   `tick`/`tick_<state>` functions, `execute if score … run function …` dispatch)
   and reconstruct one or more `Machine` objects.
3. **Python** — emit runnable builder source (`new_machine(...)`,
   `add_state`, `.enter.setblock(...)`, `.transition(...)`, `.add_transition(...)`
   `.when_score(...)`) that recreates those machines — the human-readable payoff.

## Pipeline

1. **Load** a datapack from a directory **or** a `.zip` (reuse the archive
   handling in `grimmcraft-world`/`filesystem` if present; else unzip to a temp
   dir). Locate `pack.mcmeta` and the `data/<ns>/…` tree.
2. **Detect the target.** Read `pack.mcmeta`'s `pack_format` (+ `supported_formats`)
   and the folder scheme (singular `function/` vs plural `functions/`) and resolve
   a `Target` from the compiler's version table. Fail fast / warn if the
   `pack_format` maps to no supported version, and record how confident the
   detection is.
3. **Parse commands (reverse `Dialect`).** Tokenise each line and lift it to a
   `Command`: `setblock`/`fill` → block id + `BlockPos` + state; `give` → item
   (+ read the **components** `[…]` on 1.20.5+ vs the **NBT** `{…}` before it, per
   the detected version); `execute if score … run <sub>` → the nested command;
   `function ns:path` → a `call`; `scoreboard players set/add` → `set_score`/
   `add_score`; text components (SNBT vs JSON) → their value. Keep this in one
   `Parser`/`reader` that mirrors the `Dialect` one-to-one.
4. **Build the IR** `Datapack` (functions, `minecraft:load`/`minecraft:tick`
   tags, resources).
5. **Lift to machines** (level 2): from the IR, invert `lower.py` — map state
   indices from the `init` `scoreboard players set grimmcraft_state` lines and the
   `# states: A=0, B=1` comment, read `on_<event>` dispatch tables to recover
   transitions, read `do_<source>__<event>__<target>` bodies for exit/commands/
   enter, and `tick_<state>` for cycle commands + automatic (`tick`) transitions +
   their `when_score` conditions.
6. **Emit** the requested level: pretty-print the IR, hand back `Machine`
   objects, or generate builder Python via a small code-writer.

## Diagnostics — helpful, stable codes (mirror the compiler)

A first-class `Diagnostic`/`DiagnosticBag` (reuse the compiler's), with a decompiler
code range (e.g. `GD####`), severity, message, hint and `source` (the file + line
it came from). At least:

- **Version detection (error/warning):** `pack_format` unknown, or folder scheme
  disagrees with the `pack_format` — explain the version split.
- **Unparseable command (warning):** a line the reader doesn't recognise; keep it
  as a `raw` command in the IR so nothing is lost, and say which line.
- **Not liftable to a machine (info/warning):** IR that doesn't match the
  grimmcraft convention (a hand-written pack); still return the IR, but explain
  why level-2/3 was skipped.
- **Unknown id (error) + rename "did you mean":** exactly as the compiler, via
  `grimmcraft-data` + `difflib`.
- **Ambiguous reconstruction (warning):** e.g. two states share an index.

## Round-trip guarantee (the key correctness property)

For any datapack the **compiler** produced, `compile(decompile(pack)) == pack`
byte-for-byte (same functions, tags, `pack.mcmeta`). Provide:

- a `roundtrip(pack) -> DiffReport` helper, and
- tests that take each example datapack in `grimmcraft-compiler/examples/generated/`,
  decompile → recompile, and assert equality. This doubles as a regression guard
  for the forward compiler.

For general (non-grimmcraft) packs, guarantee only **level-1** round-trip (IR →
re-render == original, modulo whitespace), and degrade gracefully.

## CLI (click + rich)

`grimmcraft-decompile` (also `python -m grimmcraft_decompiler`):
`INPUT` (a datapack dir or `.zip`), `--emit {ir,machine,python}` (default
`python`), `--output DIR/FILE`, `--version` (override auto-detection),
`--strict`, `--force`, `--dry-run`, `--roundtrip` (decompile, recompile, and
report any diff). Print the diagnostics report; exit non-zero on errors.

## Also generate — tests, examples, docs (in the package)

- **tests/** (pytest, hermetic): reverse-`Dialect` unit tests per version
  (components vs NBT, SNBT vs JSON, folder scheme, `pack_format` → `Target`);
  machine reconstruction from a known pack; the **round-trip** tests over the
  compiler's generated examples across ≥2 versions; graceful handling of a
  hand-written / unrecognised pack.
- **examples/**: decompile the committed `generated/` datapacks (lamp, spruce,
  growing-spruce, demos) back to Python and show they recompile identically.
- **docs/**: architecture (datapack → IR → machine → Python), the reader/Dialect
  symmetry, the diagnostics `GD####` index, the round-trip contract, quickstart.
  Match the repository docs tooling.

## Deliverable checklist

- `python -c "import grimmcraft_decompiler"` works; CLI runs.
- `--emit ir` works on an arbitrary datapack; `--emit machine`/`python` works on
  grimmcraft-generated packs and reconstructs equivalent machines.
- **Round-trip**: every `grimmcraft-compiler/examples/generated/*` decompiles and
  recompiles byte-identically (tested, across ≥2 versions).
- `uv run pytest` green and hermetic; examples run; docs render.
- Type-checks clean; style consistent with the other grimmcraft packages; add
  Taskfile tasks (decompile example, roundtrip, test, docs) and wire the root
  Taskfile include + `mypy_path`.
