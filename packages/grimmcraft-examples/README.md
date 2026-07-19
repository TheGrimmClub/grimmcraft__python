# grimmcraft-examples

Every runnable example, in one place, plus the datapacks they generate.

```bash
task examples:tutorial      # build a lamp machine and see how it lowers
task examples:dungeon       # capture a room, place it, decompile it back
task examples:roundtrip     # decompile + recompile every pack, assert equality
task examples:all           # run the lot (a workspace-wide smoke test)

task examples:run -- tree   # or run any module directly
```

Each example is a module, so `python -m grimmcraft_examples.<name>` works from
any directory — the paths inside resolve from `__file__`, not the cwd.

## Why they live here and not beside each package

Because the interesting examples are **cross-package**, and an example may only
honestly import what its own package declares.

`dungeon_room.py` captures a structure from a world, places it from a state
machine, compiles the pack, and then decompiles it back to check the effect
survived. That touches `grimmcraft-world`, `-structures`, `-control`,
`-compiler` and `-decompiler`. Sitting in `grimmcraft-structures/examples/` it
imported `grimmcraft_decompiler` without that package declaring the dependency —
it only ran because the workspace venv happened to have everything installed.

Collecting the examples here lets *this* package depend on everything while each
library package's dependencies stay minimal and truthful.

## What's here

| Module | Shows |
|--------|-------|
| `tutorial_lamp` | Build a machine from scratch; print the `mcfunction` it lowers to. |
| `chessboard` | Generate many blocks with a plain Python loop. |
| `tree` | Place a parametric spruce with `fill`. |
| `tree_growing` | A cycle + scoreboard machine that grows one ring per tick. |
| `compile_demos` | The demo machines compiled for 1.20.4 and 1.21.11. |
| `decompile_examples` | Every committed pack decompiled back to Python. |
| `roundtrip_examples` | Decompile → recompile → assert byte-equality. |
| `dungeon_room` | Capture → store → place → decompile, end to end. |
| `redstone_clock`, `redstone_half_adder`, `redstone_lever_lamp`, `redstone_t_flip_flop` | Simulated redstone circuits. |

## `generated/`

The committed datapacks the compiler examples produce — reference output you can
read without running anything, and the fixtures the decompiler's round-trip tests
check against.

Regenerate them with `task examples:regenerate`. They should be reproducible: if
that command leaves a diff, either an example or the compiler changed, and the
diff is the thing to look at.
