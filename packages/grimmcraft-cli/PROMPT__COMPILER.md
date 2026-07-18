# Task: build the grimmcraft → mcfunction datapack compiler
> [\] TODO: execute PROMPT__COMPILER.md 

Implement a Python compiler that lowers the grimmcraft domain model into a
**complete, installable Minecraft datapack** ready to test in-game. Put it in a
dedicated package (e.g. `packages/grimmcraft-compiler/sr/grimmcraft_compiler/`);
create it if it doesn't exist and match the repositories conventions (uv, Python
version, dataclass/pydantic choice, layout, lint/type config, Taskfile).
**First inspect all sibling packages** and reuse them — do not re-implement what
they already provide.

If you suggest a task to execute show it as a taskfile like task with a description element (`desc`).

## Use all available packages

- **grimmcraft-data** — the source of truth for the target version. Validate
  every referenced `Block`/`Item`/`Entity`/registry id against the enums for the
  chosen MC version; use it for id-exists checks, deprecation/rename detection,
  and "did you mean" suggestions.
- **grimmcraft-core** — `Coordinates`, entities, items, workstations are the
  objects the compiler emits commands for (spawn/place/setblock/give/interact).
- **grimmcraft-control** (`machine`) — compile state machines into runtime
  functions: states → scoreboard/storage values, events → trigger functions,
  transitions → guarded command sequences, emitted `Command`s → mcfunction lines.
  The machine stays the single source of behavior; the compiler is its backend.

## Target configuration — version + flavor (required setting)

A `Target` config drives everything:

```python
@dataclass(frozen=True)
class Target:
    version: str            # e.g. "1.21.11"
    flavor: Flavor          # VANILLA | PAPER | FABRIC
```

The target must resolve (data-driven, easy to extend — a table, not scattered
`if`s):

- **pack_format** for `pack.mcmeta` (map version → pack_format; support the
  `supported_formats` range where applicable). Do NOT hardcode a single value.
- **Folder scheme.** Minecraft 1.21 renamed datapack sub directories to **singular**
  (`function`, `tags/function`, `loot_table`, `recipe`, `advancement`,
  `predicate`, `item_modifier`); earlier versions use the **plural** forms.
  Select the scheme by version.
- **Command dialect.** Version-specific syntax: item/block data as **components**
  (1.20.5+) vs **NBT tags** (earlier); `execute` sub-command availability; text
  components as SNBT vs JSON; selector features. Encapsulate this in a
  `Dialect`/emitter so command rendering is version-correct in one place.
- **Flavor effects.** VANILLA = strict vanilla command set. PAPER = vanilla
  datapack semantics but allow documented Paper additions/flags where relevant.
  FABRIC = vanilla-compatible datapack (note where a Fabric mod API would be
  needed instead and warn rather than silently emit invalid commands).

Fail fast with a clear error if a version/flavor combination isn't supported.

## Compiler pipeline

1. **Collect** the domain model (functions to emit, machines, placed
   workstations, spawn setup, tags).
2. **Build an IR**: a set of `Function`s (namespaced id + ordered command list),
   plus resources (tags, loot tables, recipes) and the `load`/`tick` function-tag
   membership. Keep the IR dialect-independent.
3. **Validate** against `grimmcraft-data` for the `Target` (see diagnostics).
4. **Render** each IR command to text via the version `Dialect`.
5. **Emit** the datapack tree: `pack.mcmeta`, correct folder scheme, namespaced
   `data/<ns>/…`, `minecraft:load` + `minecraft:tick` function tags, all JSON
   resources. Optionally **zip** it.
6. **Verify** the output (see below).

## Diagnostics — errors & warnings with helpful text

A first-class diagnostics system is central to this task:

- `Diagnostic(severity, code, message, hint, source)` where `severity` ∈
  {ERROR, WARNING, INFO}, `code` is stable (e.g. `GC1001`), `source` points at
  the originating domain object / machine / transition (so the developer knows
  *where* it came from), `hint` is an actionable fix.
- Collect into a `DiagnosticBag`; render a clean, grouped, optionally colorized
  report with counts. Errors abort emission unless `--force`; `--strict` promotes
  warnings to errors.
- Messages must be genuinely helpful, e.g.:
  - **Unknown id (error):** `GC1001: item 'minecraft:grass' does not exist in
    1.21. It was renamed to 'short_grass' in 1.20.3. Did you mean
    'minecraft:short_grass'?` (use `grimmcraft-data` + `difflib` for suggestions).
  - **Version mismatch (error):** component syntax used but target < 1.20.5 →
    explain the NBT-vs-components split and the minimum version.
  - **Flavor (warning):** a command only meaningful on Paper/Fabric used with a
    different flavor → warn with the correct alternative.
  - **Unresolved reference (error):** a function calls an undefined function, or
    a function tag references a missing function.
  - **Deprecation (warning):** id valid but deprecated in the target version.
  - **Namespace/resource-location (error):** invalid characters, with the allowed
    charset shown.

Every diagnostic should tell the developer what's wrong, why, where, and how to
fix it.

## CLI
use click for the cli and rich for output formatting.
`grimmcraft-compile` (also `python -m grimmcraft_compiler`), with:
`--version`, `--flavor {vanilla,paper,fabric}`, `--namespace`, `--output DIR`,
`--zip`, `--strict`, `--force`, `--dry-run` (validate + report, emit nothing).
Exit non-zero when errors exist. Print the diagnostics report and, on success,
the output path plus install/test instructions.

## Output verification (ready for testing)

- `pack.mcmeta` has the correct `pack_format` for the target; all JSON is valid.
- Folder scheme matches the version; all resource locations are well-formed.
- Every `function` call and tag reference resolves inside the pack.
- Produce a short generated `README`/`INSTALL.md` in the output: how to install
  (drop the folder/zip into `saves/<world>/datapacks/`, run `/reload`, or place
  in a server's `datapacks/`) and how to trigger the example behavior.

## Also generate — tests, examples, docs (in the compiler package)

- **tests/** (pytest, `uv run pytest`, hermetic): dialect rendering per version
  (components vs NBT, folder scheme, pack_format), diagnostics (unknown id →
  right code + suggestion; strict mode; unresolved refs), and an end-to-end
  compile of a tiny machine to a datapack whose JSON validates and whose function
  references resolve. Parametrize across at least two versions and all flavors.
- **examples/**: compile a real grimmcraft example (e.g. the Door or Furnace
  state machine from grimmcraft-control) into a datapack, for two different
  targets (e.g. `1.20.4 vanilla` and `1.21.11 vanilla`) to show the differences.
- **docs/**: architecture overview (IR → dialect → emit), the version/flavor
  support matrix, the diagnostics code index (each `GC{id}` with meaning and
  example), and a quickstart. Match the repositories docs tooling.

## Deliverable checklist

- `python -c "import grimmcraft_compiler"` works; CLI runs.
- A generated datapack loads in the stated Minecraft version without errors
  (JSON valid, pack_format correct, folder scheme correct, references resolve).
- `uv run pytest` green and hermetic; examples produce datapacks; docs render.
- Type-checks clean; style consistent with the other grimmcraft packages; add
  Taskfile tasks (compile example, test, build docs) matching existing style.
```
