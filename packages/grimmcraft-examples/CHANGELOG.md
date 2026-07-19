# Changelog — grimmcraft-examples

## refactor(examples): collect every example into one package

New package, gathering the 12 example scripts previously spread across
`grimmcraft-compiler`, `-decompiler`, `-redstone` and `-structures`, together
with the `generated/` datapacks the compiler examples produce.

### Why they moved

Dependency honesty, not tidiness. The interesting examples are *cross-package* —
`dungeon_room` captures a structure from a world, places it from a state
machine, compiles the pack and decompiles it back — but an example may only
legitimately import what its own package declares.

Sitting in `grimmcraft-structures/examples/`, that file imported
`grimmcraft_decompiler` while structures declared no such dependency. It ran
only because the workspace virtual environment happened to have everything
installed; shipped alone, the package's own example would break.

Collecting them here lets this package depend on everything it demonstrates
while each library package's dependencies stay minimal and truthful.

### Bugs this surfaced

- `grimmcraft-npc` and `grimmcraft-migrate` each had an `example` task pointing
  at `examples/dungeon_room.py`, copied when their Taskfiles were cloned from
  grimmcraft-structures. Neither package has that file.
- `grimmcraft-npc` and `grimmcraft-structures` declared `grimmclub` and never
  imported it.
- `dungeon_room` reached into grimmcraft-structures' *test* conftest through a
  `sys.path` hack to synthesise a world. The region-writing helpers are now
  spelled out in the example itself — more robust, and better teaching material,
  since seeing the shape of an Anvil region file is rather the point.
- Because examples now live under `srcs/`, they are type-checked for the first
  time. That caught an imprecise signature in `grimmcraft-redstone`:
  `Circuit.place()` hands back exactly what it is given but was annotated as
  returning the base class, so `circuit.place(Lever(...))` lost every concrete
  method. It is now generic over the component type — fixing the library and the
  examples together.

### Shape

Examples are modules, so they run from any working directory:

    python -m grimmcraft_examples.tutorial_lamp

Paths inside resolve from `__file__` rather than the current directory, which is
what the old scripts relied on.

## chore(examples): task names

`task examples:*` replaces the per-package example tasks:

| was | now |
|-----|-----|
| `compiler:tutorial` | `examples:tutorial` |
| `compiler:chess` / `:tree` / `:grow` | `examples:chess` / `:tree` / `:grow` |
| `compiler:example` | `examples:demos` |
| `decompiler:example` | `examples:decompile` |
| `decompiler:roundtrip` | `examples:roundtrip` |
| `redstone:example -- clock` | `examples:redstone -- clock` |
| `structures:example` | `examples:dungeon` |

Plus `task examples:all` (run everything — a workspace-wide smoke test) and
`task examples:regenerate` (rebuild the committed packs, which reproduce
byte-identically).
