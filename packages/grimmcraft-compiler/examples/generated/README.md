# Generated example datapacks

**These files are generated — do not edit by hand.** They are committed as a
reference so you can browse the compiler's output (the `.mcfunction` files,
`pack.mcmeta`, folder scheme, tags) without running anything.

Regenerate them from the example scripts:

```bash
task compiler:tutorial   # -> tutorial-lamp/         (the from-scratch lamp)
task compiler:chess      # -> chessboard/            (8x8 wool board via a loop)
task compiler:tree       # -> spruce/                (procedural conifer via fill)
task compiler:grow       # -> growing-spruce/        (grows one ring per tick)
task compiler:example    # -> demo-1.20.4-vanilla/ + demo-1.21.1-vanilla/
```

Each subfolder is a complete, installable datapack — drop it into
`saves/<world>/datapacks/` and run `/reload` (see each pack's `INSTALL.md`).

| Folder | Source | Target |
|--------|--------|--------|
| `tutorial-lamp/` | `../tutorial_lamp.py` | 1.21.1 vanilla |
| `chessboard/` | `../chessboard.py` | 1.21.1 vanilla (64-block `build`, `clear` to air) |
| `spruce/` | `../tree.py` | 1.21.1 vanilla (conifer via `fill`: `grow`, `chop`) |
| `growing-spruce/` | `../tree_growing.py` | 1.21.1 vanilla (grows one ring per tick) |
| `demo-1.20.4-vanilla/` | `../compile_demos.py` | 1.20.4 vanilla (plural folders, NBT) |
| `demo-1.21.1-vanilla/` | `../compile_demos.py` | 1.21.1 vanilla (singular folders, components) |

Compare `demo-1.20.4-vanilla` vs `demo-1.21.1-vanilla` to see how the target
changes the folder scheme (`functions/` vs `function/`) and item data
(NBT `{display:{Name:…}}` vs component `[minecraft:custom_name=…]`).
