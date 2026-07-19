# Changelog — grimmcraft-structures

## feat(structures): save and restore Minecraft `.nbt` structures

New package (depends on `grimmcraft-core`, `grimmcraft-control`, `grimmcraft-world`, `grimmclub-filesystem`), under `srcs/grimmcraft_structures/`. Closes the loop needed to build a map out of predefined pieces:

    saved world -> capture() -> Structure -> .nbt -> datapack -> place template

- `structure.py` — `Structure`, `BlockState`, `Block`. The format as a value object: a palette of distinct block states plus one entry per filled position, which is why a 32³ room of mostly stone is kilobytes rather than megabytes. `read`/`write` round-trip the real format, so a file saved by a structure block can be edited in Python and handed back to the game. `offset()` and `without()` cover the common edits.
- `capture.py` — `capture(world, corner_a, corner_b)` and `WorldBlockReader`. Reads the box straight out of the Anvil region files: no server, no structure block, the world only has to be *saved*.
- `library.py` — `StructureLibrary` owns the `ns:name` ↔ `data/<ns>/structures/<name>.nbt` mapping and writes the files into an emitted pack.
- `cli.py` — `grimmcraft-structure capture` and `show`.

### Two decisions worth recording
**`None` is not air.** An ungenerated chunk, a pre-1.18 chunk layout, or a position outside the built height range all read as `None` and are *skipped*, rather than recorded as `minecraft:air`. Recording air there would make a captured piece carve a box out of the terrain it is placed into instead of blending with it. Air present in the box is dropped by default too, matching vanilla, with `include_air=True` for a sealed room.

**The palette is rebuilt on write** from the blocks in first-use order, so editing a structure in Python cannot leave it referencing states nothing uses.

`StructureLibrary` deliberately does not go through the compiler's `Resource` IR: that models JSON documents, and a structure is gzipped binary NBT. `write_into()` adds the files to an already-emitted tree instead.

## test(structures): 40 tests

The suite *writes* an Anvil region file and then captures from it — the strongest available evidence that `grimmcraft-world`'s NBT reader and its new writer agree. Plus the `.nbt` round-trip, malformed-entry handling, the library's paths and ids, and the `place` command across control → compiler → decompiler.

## docs(structures): architecture and README

`docs/architecture.md` — the three responsibilities kept apart, the NBT list-type ambiguity, and why `place` lives in the shared vocabulary. Plus a runnable `examples/dungeon_room.py` demonstrating the whole loop, ending by decompiling the pack back to the same `place` effect.
