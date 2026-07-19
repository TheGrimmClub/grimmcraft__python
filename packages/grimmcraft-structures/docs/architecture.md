# Architecture

Three responsibilities, deliberately kept apart: read a world, model a structure,
ship it in a datapack.

```
saved world (region/*.mca)
      │  capture.py      WorldBlockReader → chunk_block_state
      ▼
  Structure  ◄────────────►  .nbt file        (structure.py + grimmcraft-world.nbt)
      │  library.py      data/<ns>/structures/<name>.nbt
      ▼
  StructureLibrary ──► "ns:name" ──► place effect ──► `place template ns:name x y z`
```

## Saving — `capture.py`

`capture(world, a, b)` reads the Anvil region files directly. No server and no
structure block are involved; the world only has to be **saved**, since that is
when Minecraft flushes chunks to disk.

The work is done by `grimmcraft-world.region.chunk_block_state`, which
un-bit-packs a section's palette indices. Two things this module adds:

- **Chunk caching.** A box spanning several chunks would otherwise re-read and
  re-decompress the same chunk for every column in it. `WorldBlockReader` keeps
  parsed chunks for the duration of a capture.
- **`None` is not air.** An ungenerated chunk, a pre-1.18 chunk layout, or a
  position outside the built height range all read as `None`, and are skipped
  rather than becoming `minecraft:air`. Recording air there would make a
  structure carve a box out of the terrain it is placed into.

Air *is* dropped by default (`DEFAULT_SKIP`), matching vanilla, so a captured
piece blends into existing ground. `include_air=True` captures the box verbatim,
which is what a sealed room wants.

## Modelling — `structure.py`

`Structure` is Minecraft's format as a value object: a **palette** of distinct
`BlockState`s plus one entry per filled position holding a palette index. That
indirection is why a 32³ room of mostly stone is kilobytes, not megabytes.

The palette is **rebuilt on write** from the blocks in first-use order, so it can
never carry states nothing references — editing a structure in Python cannot
leave it inconsistent.

Positions are relative to the structure's own origin and always non-negative;
that is what makes a structure placeable anywhere.

`from_nbt` drops malformed entries (a palette index out of range, a position that
is not three coordinates) rather than guessing, because the alternative is
inventing blocks in someone's build.

## NBT writing — `grimmcraft-world.nbt`

The writer lives with the reader, not here: `grimmcraft-world` owns NBT.

The one sharp edge is that **reading is lossy about list types**. NBT
distinguishes `TAG_List` of ints from `TAG_Int_Array`, but both parse to a plain
Python `list`. Writing therefore infers from contents — a list of ints becomes a
`TAG_List` of `TAG_Int`, which is exactly what the structure format wants for
`size` and `pos`. Where the array form is required (a chunk's packed block
states), wrap the value: `IntArray`, `LongArray`, `ByteArray`, or `Long`, `Byte`,
`Short`, `Float` for the scalars.

That the test suite can *write* a region file and then capture from it is the
strongest evidence both halves agree.

## Shipping — `library.py`

`StructureLibrary` owns the mapping between the id Minecraft places by
(`namespace:name`) and the path it reads from
(`data/<namespace>/structures/<name>.nbt`).

It deliberately does **not** go through the compiler's `Resource` IR: that models
JSON documents, and a structure is gzipped binary NBT. `write_into` drops the
files into an already-emitted pack instead, after `compile_machines` has written
the tree it owns.

Note the folder is `structures` in *every* version — it was already plural and
was untouched by the 1.21 singular-folder rename that turned `functions` into
`function`.

## Placing — the shared `place` command

`place` is part of the vocabulary in `grimmcraft-control`, not something this
package renders privately. That buys three things for one small addition:

| Package | Addition |
|---------|----------|
| `grimmcraft-control` | `CommandName.PLACE`, `effects.place()`, `EffectWriter.place()` |
| `grimmcraft-compiler` | `Dialect._r_place` |
| `grimmcraft-decompiler` | `CommandReader._read_place`, codegen support |

So a placed structure validates, renders, **round-trips**, and decompiles back
into readable Python like any other effect — rather than being an opaque `raw`
line the decompiler has to give up on.

`place template`'s trailing arguments are positional, so a mirror cannot be given
without a rotation; `_r_place` inserts the neutral `none` rotation when only a
mirror is set, and reading that back yields the same command.

The effect declares `min_version="1.19"`, when `place template` replaced
`/structure load`. That is below the compiler's oldest supported target (1.20.1),
so the gate never trips today — it is carried so it fires on its own if an older
version is added to the support table.
