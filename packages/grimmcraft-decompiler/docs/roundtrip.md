# The round-trip contract

The correctness property this package is built around:

> For any datapack the **compiler** produced,
> `compile(decompile(pack)) == pack` — byte for byte.

Same functions, same tags, same `pack.mcmeta`, same `INSTALL.md`. It is checked
in CI over every committed example pack, at both levels, across two Minecraft
versions either side of every behavioural threshold.

This doubles as a regression guard on the **forward** compiler: if lowering
changes shape, these diffs light up. It has already caught one — `category_dir`
pluralised `dimension` into `dimensions`, which the game does not read.

## Two levels

| Level | What is re-emitted | Applies to |
|-------|--------------------|------------|
| `Level.IR` | the lifted `Datapack` IR, straight back through `emit()` | any datapack |
| `Level.MACHINE` | the reconstructed machines, back through the real `lower()` then `emit()` | grimmcraft-generated packs |

`Level.MACHINE` is the strict claim. It runs the genuine forward pipeline rather
than echoing the IR back, so it exercises lowering, rendering and emission.

## Two strengths

`strict=True` (the default) demands byte equality across every file. This is the
contract for compiler-generated packs.

`strict=False` is for **hand-written** packs, where the guarantee is weaker and
must be stated honestly: the modelled *content* survives, the *layout* may not.
It compares only files the IR represents, and only up to formatting:

- `.mcfunction` files are compared ignoring the trailing newline
- `.json` files are compared as parsed JSON, not as text
- files the IR has no model for (`README.md`, generator scripts, `INSTALL.md`)
  are ignored rather than counted as losses

Even at this strength, **every `.mcfunction` must reproduce exactly** — that is
what "nothing is ever lost" means, and it is asserted in the test suite.

What legitimately differs for a hand-written pack:

- `pack.mcmeta` — the emitter adds a `supported_formats` band and normalises
  indentation
- resource folder names, if the pack's scheme disagrees with its `pack_format`

## Using it

```python
from grimmcraft_decompiler import decompile, roundtrip
from grimmcraft_decompiler.roundtrip import Level

result = decompile("saves/world/datapacks/tutorial-lamp", emit="machine")
with result.source:
    report = roundtrip(
        result.source, result.pack, result.target,
        machines=result.machines, level=Level.MACHINE,
    )
    print(report.render())
```

Or from the CLI, which reports it and exits non-zero on a mismatch:

```sh
grimmcraft-decompile <pack> --roundtrip
```

`DiffReport.differences` lists every `FileDiff` as `missing` (not re-emitted),
`extra` (only re-emitted) or `changed` (with a unified diff).

## Why it holds

Because the reader is **self-verifying**. Every parse is rendered back through
the real `Dialect` and accepted only if it reproduces the source line exactly;
anything else degrades to a `raw` command, which re-emits verbatim. A parser
therefore *cannot* silently normalise a pack. See
[architecture](architecture.md#level-1--ir).

## Running the checks

```sh
task decompiler:roundtrip   # the executable demonstration, over every example
task decompiler:test        # the same property as pytest, plus the fresh-pack cases
```
