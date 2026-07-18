# grimmcraft-decompiler

Create a lower grimmcraft **state machines** (from `grimmcraft-control`) into a complete,
from a **Minecraft datapack** — validated against `grimmcraft-data` for a chosen version and flavor.


## Quickstart

```bash
# compile the demo door + furnace for 1.21.11 vanilla into dist/grimmcraft
uv run grimmcraft-decompile --version 1.21.11 --flavor vanilla

# validate only, promote warnings to errors, no output written
uv run grimmcraft-decompile --version 1.20.4 --strict --dry-run

# list supported versions
uv run grimmcraft-decompile --list-versions
```

Also runnable as `python -m grimmcraft_decompiler`.

## What it does

- **Target = version + flavor.** `pack_format`, the datapack folder scheme
  (singular `function/` on 1.21+, plural `functions/` earlier) and the command
  dialect (item/block **components** on 1.20.5+ vs **NBT** before; text as SNBT
  vs JSON) are all resolved from a data-driven table — see
  [`docs/support-matrix.md`](docs/support-matrix.md).
- **Machines from functions.** States → a `grimmcraft_state` scoreboard value;
  events → `on_<event>` trigger functions; transitions → guarded `do_…`
  sequences; a state's per-tick **cycle** commands and automatic `tick`
  transitions → the machine's `tick` function.
- **Diagnostics are first-class.** Unknown ids (with rename detection and
  "did you mean" suggestions), version/flavor mismatches, unresolved references
  and bad resource locations each get a stable `GC####` code — see
  [`docs/diagnostics.md`](docs/diagnostics.md).

## Docs
TODO: add / remove as needed
- [Tutorial](docs/tutorial.md) — build a machine from scratch and see how it lowers.
- [Architecture](docs/architecture.md) — IR → dialect → emit.
- [Support matrix](docs/support-matrix.md) — versions, pack formats, flavors.
- [Diagnostics index](docs/diagnostics.md) — every `GC####` with an example.
- [Quickstart](docs/quickstart.md).

## Develop
TODO: add / remove as needed
```bash
task decompiler:test      # pytest (hermetic)
task decompiler:example   # compile the demos for 1.20.4 and 1.21.11
task decompiler:typecheck # mypy
```
