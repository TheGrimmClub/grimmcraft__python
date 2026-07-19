# grimmcraft-structures

Save and restore Minecraft **structures** — the `.nbt` templates a structure
block writes — so a datapack can build a map out of predefined pieces.

```bash
# save a box of blocks straight out of a saved world
uv run grimmcraft-structure capture saves/MyWorld \
    --from 0 64 0 --to 8 70 8 -o rooms/dungeon_room.nbt

# see what's in a structure file
uv run grimmcraft-structure show rooms/dungeon_room.nbt
```

```python
from grimmcraft_core import BlockPos
from grimmcraft_control import new_machine
from grimmcraft_structures import StructureLibrary, capture

# 1. save — read a box out of a saved world (no server, no structure block)
room = capture("saves/MyWorld", BlockPos(0, 64, 0), BlockPos(8, 70, 8))

# 2. store — register it under a datapack namespace
library = StructureLibrary("dungeon")
library.add("room", room.without("minecraft:air"))

# 3. restore — place it from a machine
builder = new_machine("dungeon")
with builder.add_state("BUILT") as built:
    built.enter.place(library.id("room"), BlockPos(0, 64, 0))
```

After compiling, drop the files into the emitted pack:

```python
result = compile_machines([machine], target, namespace="dungeon")
library.write_into(result.output_path)   # data/dungeon/structures/room.nbt
```

The machine lowers to `place template dungeon:room 0 64 0`.

## What it does

- **`capture(world, a, b)`** reads the box between two corners directly out of
  the world's Anvil region files via `grimmcraft-world`. The world only has to
  be *saved* — no running server, no structure block. Air is dropped by default,
  matching vanilla, so a captured piece blends into existing terrain.
- **`Structure`** is the `.nbt` format as a value object: a palette of distinct
  block states plus one entry per filled position. `read`/`write` round-trip the
  real format, so a file saved by a structure block can be edited in Python and
  handed back to the game. `offset` and `without` cover the common edits.
- **`StructureLibrary`** owns the `namespace:name` ↔ `data/<ns>/structures/<name>.nbt`
  mapping and writes the files into an emitted datapack.
- **`place`** is part of the shared command vocabulary in `grimmcraft-control`,
  so the compiler renders it, the decompiler reads it back, and it round-trips
  like any other effect.

## Notes

- `place template` needs **Minecraft 1.19+**. The effect declares that, so
  compiling for an older target reports `GC1005` rather than emitting a command
  the game will reject.
- The `structures` folder name did **not** change in the 1.21 singular-folder
  rename — it was already `structures` and stayed there.
- `DataVersion` defaults to 1.21.11's. Minecraft runs its data fixers on an
  older value, but refuses a *newer* one, so set it when targeting older games.

## NBT writing

`grimmcraft-world.nbt` gained a writer for this (`dump` / `save`). NBT
distinguishes a `TAG_List` of ints from a `TAG_Int_Array`, but reading collapses
both to a Python `list` — so wrap a value in `IntArray`, `LongArray`, `ByteArray`
(or `Long`, `Byte`, `Short`, `Float`) to force the exact tag. The structure
format wants plain lists, so the defaults are already right.

## Tasks

```sh
task structures:test        # run the tests
task structures:lint        # ruff
task structures:typecheck   # mypy
```
