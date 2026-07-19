# Changelog — grimmcraft-world

## feat(world): import from grimmcraft__town as `grimmcraft-world`

Moved out of `TheGrimmClub/grimmcraft__town` (where it was `minecraft`) and renamed. Reads the interesting facts out of a Minecraft world, under `srcs/grimmcraft_world/`. Depends on `grimmclub-filesystem`.

- `nbt.py` — a dependency-free NBT reader (gzip/zlib auto-detected).
- `region.py` — the Anvil `.mca` reader: `iter_region_chunks`, `chunk_block_state` (un-bit-packs a section's palette indices), `chunk_block_entities`, `iter_block_entities`.
- `world.py` — `locate_world`, `read_world_info`, `discover_datapacks`.

## feat(world): NBT writer

`nbt.py` gained `dump()` / `save()` — it was read-only, and writing a structure file needs the other direction.

Reading is lossy about list types: NBT distinguishes `TAG_List`-of-int from `TAG_Int_Array`, but both parse to a Python `list`. Writing therefore infers the tag from the contents (a list of ints becomes `TAG_List` of `TAG_Int`, which is what the structure format wants), with `IntArray` / `LongArray` / `ByteArray` and `Long` / `Byte` / `Short` / `Float` wrappers to force an exact tag where it matters — a chunk's packed block states, for instance.

## feat(world): expect_nbt / expect_keys

Validation to match `grimmclub-filesystem`'s `expect_json`. A truncated or non-NBT file otherwise surfaces as a bare `EOFError` from deep inside the parser, saying nothing about which file is at fault. `expect_keys` names *every* missing key at once, because fixing a hand-edited file one error per run is what makes schema errors miserable.

## feat(world): read_chunk / region_file

Look up a single chunk by coordinate rather than scanning a whole region file — what `grimmcraft-structures`' capture needs to read a box of blocks.

## refactor(world): repo conventions

`srcs/` layout, `uv_build` backend, absolute imports, `py.typed`, a `Taskfile.yml` (`world:` namespace), and mypy `--strict` clean.
