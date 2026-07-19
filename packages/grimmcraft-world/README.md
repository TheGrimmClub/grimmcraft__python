# grimmcraft-world

Read the interesting facts out of a Minecraft world folder: the NBT reader, the
Anvil region reader, and a friendly world summary (name, version, datapacks).

Built on [`grimmclub-filesystem`](../grimmclub-filesystem) for path and archive
handling, so this package only holds the *Minecraft-specific* knowledge.

```python
from grimmcraft_world.world import locate_world, read_world_info

world = locate_world("./_input")      # the folder containing level.dat
info = read_world_info(world)
print(info.name, info.version, [pack.name for pack in info.datapacks])
```

## Modules

| Module | What it does |
|--------|--------------|
| `nbt` | A dependency-free reader for Minecraft's NBT format (gzip/zlib auto-detected). |
| `region` | The Anvil `.mca` region reader — locate and decode chunks. |
| `world` | `locate_world`, `read_world_info` and datapack discovery. |

`discover_datapacks` pairs naturally with
[`grimmcraft-decompiler`](../grimmcraft-decompiler): find the packs installed in
a world, then decompile one back to Python.

## Tasks

```sh
task world:test        # run the tests
task world:lint        # ruff
task world:typecheck   # mypy
```
