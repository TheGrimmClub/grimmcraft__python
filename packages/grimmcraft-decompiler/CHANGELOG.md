# Changelog — grimmcraft-decompiler

## feat(decompiler): lift datapacks back into the grimmcraft model

The inverse of `grimmcraft-compiler`, under `srcs/grimmcraft_decompiler/`. Three levels that degrade into each other rather than failing:

1. **IR** — every `.mcfunction` line back into a declarative `Command`, plus tags and resources. Works on *any* datapack.
2. **Machine** — recognise the lowering conventions and rebuild the `Machine` objects.
3. **Python** — emit runnable builder source that recreates them.

Nothing is forked from the compiler: the same IR, `Target` table, `Dialect` and diagnostics machinery, so a version quirk stays fixed in one place.

### Modules
- `source.py` — load a datapack from a directory or `.zip` (via `grimmclub-filesystem`'s archive handling), descending into a single wrapping folder.
- `detect.py` — resolve the `Target` from three signals, strongest first: the version tail the compiler writes into the pack description, the `pack_format` / `min_format`, and the folder scheme. Records a `Confidence`, because format 48 is both 1.21 and 1.21.1.
- `reader.py` — the inverse of `dialect.py`, one `_read_<verb>` per `_r_<name>`.
- `lift_ir.py` — functions, tags and JSON resources into a `Datapack`.
- `lift_machine.py` — inverts `lower.py`.
- `codegen.py` — builder Python via a small code-writer.
- `roundtrip.py` — `roundtrip()` and `DiffReport`.
- `decompiler.py` / `cli.py` — the pipeline and the `grimmcraft-decompile` command.

### The reader verifies itself
Every parse is rendered back through the real `Dialect` and accepted only if it reproduces the line byte-for-byte; anything else degrades to a `raw` command, which re-emits verbatim.

That inverts the burden of proof. A parser *cannot* silently normalise a pack — drop a trailing space, reformat a `### banner ###` comment, rewrite `07` as `7` — because the check catches it and falls back. Level-1 byte fidelity is structural rather than a matter of care in each parser, and `raw` is what makes "nothing is ever lost" true for commands the IR has no model for.

### Machine lifting
The `grimmcraft_state` write is an unambiguous fence: everything after it is the target state's enter block, recovered exactly. Everything before it is the source's exit block concatenated with the transition's own commands, and that boundary was never recorded — so the exit block is recovered as the longest common prefix across every transition leaving that state.

With a single outgoing transition the split is genuinely undecidable; everything is attributed to the state's exit and `GD2004` says so. Both readings re-lower to identical bytes, so only the naming in the generated Python differs.

Names survive because the compiler already writes them into comments: `# states: OFF=0, ON=1` recovers the casing the path slug destroyed, and `# OFF --pull--> ON` recovers each transition's source, event and target.

## test(decompiler): 114 tests, including the round-trip contract

`compile(decompile(pack)) == pack`, byte for byte, over every committed example pack, at both levels, across two versions either side of the folder / component / SNBT thresholds. Fixtures are compiled fresh by the suite, so it is hermetic; the committed packs are exercised separately, which is where drift shows up.

Reverse-`Dialect` unit tests per version (components vs NBT, SNBT vs JSON, positions, blank lines, comments, the `raw` fallback), machine reconstruction against the original machines, generated Python that is executed and recompiled, and graceful handling of a hand-written pack.

## docs(decompiler): architecture, round-trip, diagnostics, quickstart

`docs/` — the datapack → IR → machine → Python pipeline and what is honestly *not* recoverable (enum identity, machine-name casing, `for_entity`, runtime guards); the round-trip contract and its two strengths; the `GD####` index; the support matrix and detection signals. Plus a rewritten `README.md` and two runnable `examples/` (decompile all committed packs, round-trip all committed packs).

## build(decompiler): package manifest and tasks

`pyproject.toml` — the `grimmcraft-decompile` script (was a copy-pasted `compile`), plus a `grimmclub-filesystem` dependency for archive handling. `Taskfile.yml` adds the `decompiler:` namespace (`test`, `lint`, `typecheck`, `example`, `roundtrip`, `lamp`, `run`, `docs`).
