# Diagnostics index

Every problem the decompiler reports carries a stable `GD####` code, a severity,
a `source` (the file and line it came from) and an actionable `hint`. The
machinery is the compiler's — same `Diagnostic`, `DiagnosticBag` and `Severity` —
so a decompile report reads exactly like a compile report and the two can share
one bag. Codes are defined in `diagnostics.py` (`Codes`).

`--strict` promotes warnings to errors; errors suppress writing output unless
`--force`. The CLI exits non-zero when any error is present.

Compiler codes are `GC####`; decompiler codes are `GD####`, so a mixed report is
never ambiguous about which direction produced a message.

## Errors

### `GD1001` — Unknown pack format
The `pack_format` (or `min_format`) maps to no supported Minecraft version, so
no `Target` could be resolved from it. Detection falls back to the newest version
matching the folder scheme and continues.

> `GD1001: pack format 10 does not map to any supported Minecraft version`
> — hint: `pass --version to decompile anyway; supported versions are: 1.20.1, …`

### `GD1002` — Missing or invalid pack.mcmeta
The pack root has no `pack.mcmeta`, it is not valid JSON, or it has no `pack`
object. Usually means the path points one level too high or too low.

> `GD1002: 'pack.mcmeta' not found at the pack root`
> — hint: `point at the datapack folder itself (the one containing pack.mcmeta)`

### `GD1003` — Unknown registry id
A recovered `Block`/`Item`/`Entity` id does not exist in the detected version.
Backed by `grimmcraft-data`, the same curated rename table the compiler uses, and
`difflib` for suggestions — so the message matches `GC1001` exactly.

### `GD1004` — Datapack has no data/ directory
The pack defines nothing. A datapack stores everything under `data/<namespace>/`.

### `GD1005` — Round-trip produced a different pack
Raised by `--roundtrip` when re-emitting the decompiled result does not reproduce
the original. Either the pack was edited after compilation, or the reader and the
`Dialect` have drifted apart — the report names every differing file.

## Warnings

### `GD2001` — Folder scheme disagrees with pack_format
The tree uses singular `function/` folders but the format says pre-1.21 (or the
reverse). Minecraft renamed the datapack resource folders to their singular form
in 1.21, so one of the two signals is wrong.

> `GD2001: the tree uses singular 'function/' folders, but pack format 26 (1.20.4)
> expects plural 'functions/'`

### `GD2002` — Unrecognised command line
A line the reader cannot model declaratively. It is kept verbatim as a `raw`
command, so it re-emits unchanged and nothing is lost — but `--emit
machine`/`python` cannot interpret it. Expected in bulk on hand-written packs.

> `GD2002: cannot model this command declaratively: summon firework_rocket ~ ~1 ~ {LifeTime:45,…`

### `GD2003` — Ambiguous version detection
Several supported versions share this `pack_format` (48 is both 1.21 and 1.21.1)
and the description carries no hint. The newest candidate is assumed.

> `GD2003: pack format 48 is shared by 1.21, 1.21.1; assuming 1.21.1`
> — hint: `pass --version to pin one (e.g. --version 1.21)`

### `GD2004` — Ambiguous machine reconstruction
The IR admits more than one reading. Raised for: two states claiming the same
scoreboard index; a state entered with different command sequences by different
paths; a `do_…` function that no dispatcher reaches; and the common case — a
state with a single outgoing transition, where the exit/commands split cannot be
decided (see [architecture](architecture.md)).

### `GD2005` — Item data model disagrees with the detected version
Item data is written as NBT tags on a components-era target, or vice versa.
Minecraft moved item data from NBT to components in 1.20.5.

### `GD2006` — Deprecated id
The id exists but is discouraged in the detected version. Mirrors `GC2001`.

### `GD2007` — Ambiguous pack namespace
The pack defines functions in several namespaces, so which one *names* the pack
is a guess (the alphabetically first is used). Harmless — the namespace only
labels the pack, and every function keeps its own.

## Info

### `GD3001` — Not liftable to a machine
The IR does not follow the grimmcraft lowering convention, so levels 2 and 3 were
skipped and the IR was returned instead. Expected for any hand-written pack.

> `GD3001: no '<machine>/init' function found, so this pack does not follow the
> grimmcraft state-machine convention`
> — hint: `--emit ir works on any datapack; --emit machine/python needs a pack
> produced by grimmcraft-compile`

### `GD3002` — Decompilation summary
Function, tag and machine counts, the resolved target, and the detection
confidence. Purely informational.
