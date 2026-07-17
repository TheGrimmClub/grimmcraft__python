# Diagnostics index

Every problem the compiler reports carries a stable `GC####` code, a severity, a
`source` (which machine / transition / function it came from) and an actionable
`hint`. Errors abort emission unless `--force`; `--strict` promotes warnings to
errors. Codes are defined in `diagnostics.py` (`Codes`).

## Errors

### `GC1001` — Unknown registry id
A referenced `Block`/`Item`/`Entity` id does not exist in the target version.
Uses `grimmcraft-data` for existence, a curated table for historic renames, and
`difflib` for suggestions.

> `GC1001: block 'minecraft:grass' does not exist in 1.21.1. It was renamed to
> 'minecraft:short_grass' in 1.20.3. Did you mean 'minecraft:short_grass'?`
> — hint: `use 'minecraft:short_grass'`

### `GC1002` — Invalid resource location
A namespace or path contains characters outside the allowed set (`[a-z0-9_.-]`
for namespaces, `[a-z0-9_./-]` for paths).

> `GC1002: invalid namespace 'Bad NS': namespace 'Bad NS' has invalid characters; allowed: [a-z0-9_.-]`

### `GC1003` — Unresolved function reference
A function `call`s another function that the pack does not define.

> `GC1003: function 'grimmcraft:door/on_open' calls 'grimmcraft:door/do_x', which the pack does not define`

### `GC1004` — Unresolved function-tag member
A function tag (e.g. `minecraft:load`) lists a function that is not emitted.

### `GC1005` — Feature unavailable in target version
A command needs a newer version than the target — e.g. item/block **components**
on a pre-1.20.5 target, where data must be NBT tags.

> `GC1005: item/block components are only available from 1.20.5; before that, data must be written as NBT tags (target is 1.20.4)`

### `GC1006` — Unknown command (cannot lower)
A command or transition condition the dialect/lowering does not understand (e.g.
an unsupported `Condition` kind).

### `GC4001` — Output verification failed
The emitted tree failed a post-write check: wrong `pack_format`, wrong folder
scheme, invalid JSON, or a dangling call/tag reference on disk.

## Warnings

### `GC2001` — Deprecated id
The id exists but is discouraged in the target version.

### `GC2002` — Command not portable to this flavor
A command flagged for another flavor — `requires_flavor="paper"` on a vanilla
target, or `requires_mod_api` on Fabric (which a datapack cannot satisfy).

### `GC2003` — Runtime guard cannot be compiled
A transition has a Python `guard` but no declarative `Condition`; it is emitted
as an *unconditional* transition. Add a `Condition` (e.g. `score_matches`) to
guard it in the datapack.

### `GC2004` — Machine has no transitions
The machine would do nothing once loaded.

## Info

### `GC3001` — Compilation summary
The machine / function / tag counts for the compile. Purely informational.
