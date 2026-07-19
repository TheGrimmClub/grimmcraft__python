# Architecture

The decompiler is the compiler run backwards, and it is built as a mirror of it
on purpose: the same IR, the same `Target`/version table, the same `Dialect`, the
same diagnostics machinery. Nothing is forked. When the compiler learns a new
command, the reader is the only place that needs a matching parser.

```
datapack (dir or .zip)
      │  source.py      load files, descend into a wrapping folder
      ▼
  PackSource
      │  detect.py      pack.mcmeta + folder scheme + description → Target
      ▼
  Detection ─────────────────────────────────► Target, description, confidence
      │  reader.py      one mcfunction line → one declarative Command
      │  lift_ir.py     functions, tags, resources
      ▼
  Datapack (the compiler's IR)                            ◄── level 1
      │  lift_machine.py   invert lower.py
      ▼
  list[Machine]                                           ◄── level 2
      │  codegen.py     builder API source
      ▼
  Python module                                           ◄── level 3
```

Each level degrades into the one below. A pack that is not a grimmcraft pack
still produces the IR; a pack whose `pack_format` is unknown still produces
functions. Only an unreadable input is fatal.

## Level 1 — IR

`reader.py` is the inverse of `dialect.py`, one `_read_<verb>` per `_r_<name>`.
It works on **any** datapack.

The reader is **self-verifying**. Every parse is rendered back through the real
`Dialect` and accepted only if it reproduces the original line byte for byte:

```python
command = self._parse(line.strip(), source=source)
if command is not None and self._reproduces(command, line):
    return command
return Command(CommandName.RAW, {"text": line})
```

This inverts the burden of proof. A parser cannot silently normalise a pack —
drop a trailing space, reformat `### banner ###`, rewrite `07` as `7` — because
the check catches it and falls back to `raw`, which re-renders verbatim. The
byte-fidelity of level 1 is therefore *structural*, not a matter of having
written each parser carefully.

`raw` is the escape hatch that makes "nothing is ever lost" true. A hand-written
pack full of `summon` commands carrying big NBT payloads still round-trips; those
lines simply stay unstructured, and `GD2002` says which.

## Level 2 — Machine

`lift_machine.py` inverts `lower.py`. Lowering emits a transition as:

```
<source state's exit commands>
<the transition's own commands>
scoreboard players set <machine> grimmcraft_state <target index>
<target state's enter commands>
```

The state write is an unambiguous fence. Everything after it is the target's
enter block, recovered exactly. Everything before it is two concatenated lists
whose boundary was never recorded — so the exit block is computed as the
**longest common prefix across every transition leaving that state**, and each
remainder is that transition's own commands.

With a single outgoing transition the split is genuinely undecidable. Everything
is then attributed to the state's exit and `GD2004` says so. Both choices
re-lower to identical bytes, so the round-trip still holds; what is lost is only
which *name* the author gave the commands.

Names survive because the compiler writes them into comments — this is the
"keep some knowledge of the original code" mechanism, and it already existed:

| Comment | Recovers |
|---------|----------|
| `# states: OFF=0, ON=1` | state names (original casing) and their indices |
| `# OFF --pull--> ON` | a transition's source, event and target |
| `# Tick while in ON` | which state a `tick_<state>` body belongs to |

Without them the path slug (`do_off__pull__on`) would have destroyed the casing
and the event name. A pack with those comments stripped reports `GD3001` and
falls back to level 1.

Guard conditions live at the *call site*, not in the transition function, so the
dispatchers (`on_<event>`, `tick_<state>`) — not the `do_…` files — are the
source of truth for ordering and for `when_score` guards.

## Level 3 — Python

`codegen.py` writes builder source: `new_machine`, `add_state`,
`.enter.setblock(...)`, `.transition(...)`, `.when_score(...)`. Effects go
through `EffectWriter` methods wherever one exists, since legibility is the whole
point; anything without a method falls back to passing a `Command` to the
writer's call form, which keeps even a `raw` line runnable.

## What is *not* recoverable

Honest limits, all of them irrelevant to behaviour:

- **Enum identity.** An author's `Block.REDSTONE_LAMP` comes back as
  `'minecraft:redstone_lamp'`. The pack only ever recorded the string.
- **Machine name casing.** `slug()` lower-cases it on the way out and it is never
  written anywhere else. `slug(slug(x)) == slug(x)`, so round-trips are stable.
- **`for_entity`.** Never emitted, so never recovered.
- **Runtime guards.** Python callables were never in the pack; only declarative
  `Condition`s survive.
- **The exit/commands split** for single-outgoing-transition states (above).

## Reuse

| From | What |
|------|------|
| `grimmcraft-compiler` | `Datapack`/`Function`/`FunctionTag`/`ResourceLocation` IR, `Target`/`VersionInfo` table, `Dialect` (as the verifier), `Diagnostic`/`DiagnosticBag`, `lower`/`emit` for the round-trip |
| `grimmcraft-control` | `Machine`, `MachineBuilder`, `Command`, `Condition` — the reconstruction target |
| `grimmcraft-core` | `BlockPos` for parsed integer positions |
| `grimmclub-filesystem` | archive handling for `.zip` input |
| `grimmclub` | the standard-library facade used by the examples |
