# grimmcraft-decompiler

Lift an installed **Minecraft datapack** back into the grimmcraft model — the
inverse of `grimmcraft-compiler`. Recover the state machines behind a pack, and
write them out as the Python that could have built them.

## Quickstart

```bash
# reconstruct builder Python from a datapack (a folder or a .zip)
uv run grimmcraft-decompile packages/grimmcraft-compiler/examples/generated/tutorial-lamp

# inspect what the parser saw — works on any datapack, grimmcraft or not
uv run grimmcraft-decompile <pack> --emit ir

# decompile, recompile, and prove the bytes match
uv run grimmcraft-decompile <pack> --roundtrip

# list supported versions
uv run grimmcraft-decompile --list-versions
```

Also runnable as `python -m grimmcraft_decompiler`.

## Three levels

| `--emit` | Produces | Works on |
|----------|----------|----------|
| `ir` | every line as a declarative `Command`, plus tags and resources | **any** datapack |
| `machine` | the reconstructed `Machine` objects | grimmcraft-generated packs |
| `python` *(default)* | runnable builder source | grimmcraft-generated packs |

Each level degrades into the one below. A hand-written pack still yields the IR,
with an explanation of why levels 2–3 were skipped — it never just fails.

## What it does

- **Detects the target.** `pack_format` (or `min_format` on 1.21.9+), the folder
  scheme, and the version tail the compiler writes into the pack description
  together resolve a `Target` — with a recorded confidence, because format 48 is
  both 1.21 and 1.21.1. See [`docs/support-matrix.md`](docs/support-matrix.md).
- **Reads commands backwards.** One parser per `Dialect` renderer. Every parse is
  **verified by re-rendering it**, so a line can never be silently normalized;
  what cannot be modelled is preserved verbatim as `raw`.
- **Rebuilds machines.** Inverts `lower.py`: the `grimmcraft_state` writes,
  `on_<event>` dispatch tables, `do_…` bodies and `tick_<state>` loops become
  states, transitions, guards and cycle commands again.
- **Diagnostics are first-class.** Version ambiguity, unparseable lines,
  non liftable packs, unknown ids and ambiguous reconstructions each get a stable
  `GD####` code — see [`docs/diagnostics.md`](docs/diagnostics.md).

## The round-trip guarantee

For any datapack the compiler produced, `compile(decompile(pack)) == pack`, byte
for byte. Verified in CI over every committed example pack, at both levels,
across two Minecraft versions. It doubles as a regression guard on the forward
compiler — it has already caught one bug there. See
[`docs/roundtrip.md`](docs/roundtrip.md).

For hand-written packs the guarantee is weaker but still stated precisely: every
`.mcfunction` reproduces exactly; formatting the emitter normalizes may not.

## Docs

- [Quickstart](docs/quickstart.md) — decompile something in one command.
- [Architecture](docs/architecture.md) — datapack → IR → machine → Python, and
  what is honestly *not* recoverable.
- [Round-trip contract](docs/roundtrip.md) — the correctness property and how to
  check it.
- [Support matrix](docs/support-matrix.md) — versions, pack formats, detection
  signals.
- [Diagnostics index](docs/diagnostics.md) — every `GD####` with an example.

## Develop

```bash
task decompiler:test       # pytest (hermetic)
task decompiler:roundtrip  # decompile + recompile every example, assert equality
task decompiler:example    # decompile the examples into dist/decompiled/
task decompiler:typecheck  # mypy
task decompiler:lint       # ruff
```
