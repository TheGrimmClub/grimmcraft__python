# grimmcraft compiler — grimmcraft → mcfunction datapack

The compiler lowers the grimmcraft domain model into a **complete, installable
Minecraft datapack** ready to test in-game. It is a *backend*: the behavior lives
in the other packages (core objects and state-machine `Command`s), and the
compiler only translates that into version-correct `.mcfunction` files and
datapack resources.

## Where it sits

- **grimmcraft-data** is the source of truth for the target version — every
  referenced `Block` / `Item` / `Entity` / registry id is validated against it.
- **grimmcraft-core** supplies the objects the compiler emits commands for
  (spawn / place / setblock / give / interact).
- **grimmcraft-control** (`machine`) supplies behavior: states become
  scoreboard/storage values, events become trigger functions, transitions become
  guarded command sequences, and emitted `Command`s become mcfunction lines.

## Target configuration — version + flavor

A single `Target` drives everything:

```python
@dataclass(frozen=True)
class Target:
    version: str            # e.g. "1.21.1"
    flavor: Flavor          # VANILLA | PAPER | FABRIC
```

The target resolves (from data-driven tables, not scattered conditionals):

- **pack_format** for `pack.mcmeta` — mapped from the version, with
  `supported_formats` ranges where applicable. Never hardcode a single value; it
  changes almost every release.
- **Folder scheme** — Minecraft **1.21 renamed datapack subfolders to singular**
  (`function`, `tags/function`, `loot_table`, `recipe`, `advancement`,
  `predicate`, `item_modifier`); earlier versions use the plural forms. Selected
  by version.
- **Command dialect** — version-specific syntax, isolated in one place: item and
  block data as **components** (1.20.5+) vs **NBT tags** (earlier), `execute`
  sub-command availability, text components as SNBT vs JSON, selector features.
- **Flavor** — `VANILLA` is the strict vanilla command set; `PAPER` allows
  documented Paper additions where relevant; `FABRIC` stays vanilla-datapack
  compatible and warns where a mod API would be required instead.

An unsupported version/flavor combination fails fast with a clear error.

## Pipeline

1. **Collect** the domain model (functions, machines, placed workstations, spawn
   setup, tags).
2. **Build an IR** — a set of `Function`s (namespaced id + ordered command list)
   plus resources (tags, loot tables, recipes) and `load` / `tick` function-tag
   membership. The IR is dialect-independent.
3. **Validate** against grimmcraft-data for the `Target`.
4. **Render** each IR command to text via the version `Dialect`.
5. **Emit** the datapack tree — `pack.mcmeta`, correct folder scheme, namespaced
   `data/<ns>/…`, `minecraft:load` + `minecraft:tick` tags, all JSON resources —
   optionally zipped.
6. **Verify** the output.

Keeping the IR separate from the dialect is what makes one model compile cleanly
to several Minecraft versions.

## Diagnostics — errors & warnings

Diagnostics are a first-class feature. Each carries a severity
(`ERROR` / `WARNING` / `INFO`), a stable code (e.g. `GC1001`), a `source`
pointing at the originating domain object / machine / transition, and an
actionable `hint`. They collect into a bag and render as a grouped report;
errors abort emission unless `--force`, and `--strict` promotes warnings to
errors.

Representative messages:

| Code     | Severity | Example |
|----------|----------|---------|
| `GC1001` | error    | `item 'minecraft:grass' does not exist in 1.21. It was renamed to 'short_grass' in 1.20.3. Did you mean 'minecraft:short_grass'?` |
| `GC1010` | error    | component syntax used but target < 1.20.5 — explains the NBT-vs-components split and the minimum version |
| `GC1020` | error    | a function calls an undefined function, or a tag references a missing function |
| `GC2001` | warning  | id is valid but deprecated in the target version |
| `GC2010` | warning  | a Paper/Fabric-only command used with a different flavor, with the correct alternative |
| `GC1030` | error    | invalid namespace / resource location, with the allowed charset shown |

Unknown-id suggestions come from grimmcraft-data plus `difflib`. Every diagnostic
tells the developer *what* is wrong, *why*, *where*, and *how to fix it*.

## CLI

```
grimmcraft-compile --version 1.21.1 --flavor vanilla --namespace grimm \
                   --output build/ [--zip] [--strict] [--force] [--dry-run]
```

`--dry-run` validates and reports without emitting. The tool exits non-zero when
errors exist, prints the diagnostics report, and on success prints the output
path plus install/test instructions.

## Output & testing

A produced datapack is verified so that:

- `pack.mcmeta` has the correct `pack_format` for the target and all JSON is
  valid,
- the folder scheme matches the version and all resource locations are
  well-formed,
- every `function` call and tag reference resolves inside the pack.

To test it, drop the folder (or zip) into `saves/<world>/datapacks/` and run
`/reload`, or place it in a server's `datapacks/` directory. A generated
`INSTALL.md` accompanies each build with the exact steps and how to trigger the
example behavior.

## Why version/flavor matters (the traps this avoids)

- **The 1.21 singular-folder rename** — a pack built with the wrong scheme loads
  on one version and is silently invisible on another.
- **Components vs NBT** (the 1.20.5 item-data overhaul) — the same command has
  entirely different syntax by version, so it is isolated in the `Dialect`.
- **pack_format as a table** — hardcoding it breaks on the next release.
- **Cross-version id validation** via grimmcraft-data — catches renames like
  `grass` → `short_grass` before they reach the game.
