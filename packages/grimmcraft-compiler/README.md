# grimmcraft-compiler

Lower grimmcraft **state machines** (from `grimmcraft-control`) into a complete,
installable **Minecraft datapack** — validated against `grimmcraft-data` for a
chosen version and flavor.

```
collect machines → build IR → validate → render (dialect) → emit tree → verify
```

## Quickstart

```bash
# compile the demo door + furnace for 1.21.1 vanilla into dist/grimmcraft
uv run grimmcraft-compile --version 1.21.1 --flavor vanilla

# validate only, promote warnings to errors, no output written
uv run grimmcraft-compile --version 1.20.4 --strict --dry-run

# list supported versions
uv run grimmcraft-compile --list-versions
```

Also runnable as `python -m grimmcraft_compiler`.

## What it does

- **Target = version + flavor.** `pack_format`, the datapack folder scheme
  (singular `function/` on 1.21+, plural `functions/` earlier) and the command
  dialect (item/block **components** on 1.20.5+ vs **NBT** before; text as SNBT
  vs JSON) are all resolved from a data-driven table — see
  [`docs/support-matrix.md`](docs/support-matrix.md).
- **Machines become functions.** States → a `grimmcraft_state` scoreboard value;
  events → `on_<event>` trigger functions; transitions → guarded `do_…`
  sequences; a state's per-tick **cycle** commands and automatic `tick`
  transitions → the machine's `tick` function.
- **Diagnostics are first-class.** Unknown ids (with rename detection and
  "did you mean" suggestions), version/flavor mismatches, unresolved references
  and bad resource locations each get a stable `GC####` code — see
  [`docs/diagnostics.md`](docs/diagnostics.md).

## Docs

- [Architecture](docs/architecture.md) — IR → dialect → emit.
- [Support matrix](docs/support-matrix.md) — versions, pack formats, flavors.
- [Diagnostics index](docs/diagnostics.md) — every `GC####` with an example.
- [Quickstart](docs/quickstart.md).

## Develop

```bash
task compiler:test      # pytest (hermetic)
task compiler:example   # compile the demos for 1.20.4 and 1.21.1
task compiler:typecheck # mypy
```
