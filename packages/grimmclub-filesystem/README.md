# grimmclub-filesystem

The one interface to the file world — `os`, `pathlib`, `zipfile`, `ftplib` and
`urllib` behind a small, learner-friendly surface.

Instead of importing five standard-library modules all over the place, the
grimmcraft tools import *this* package, so "how do I touch files, archives and
remote servers" lives in one documented place.

```python
from grimmclub_filesystem import archive, paths, transfer

world = paths.locate_directory("./_input")        # a folder containing level.dat
archive.create_archive(world, "out/", archive_name="world")
transfer.download("https://host/world.zip", "in/world.zip")
```

## Modules

| Module | What it does |
|--------|--------------|
| `core` | Shared aliases (`SystemPath`, `path_like`) and the `yes`/`no` constants. |
| `paths` | Find folders by marker file, create directories, skip macOS junk. |
| `archive` | Create/extract/list zip archives without `__MACOSX` clutter. |
| `transfer` | Download over HTTP(S) and FTP, including a YAML-describable `fetch`. |
| `config` | Load/save the shared `config.yaml`, with a `.bak` safety net. |

Minecraft-specific reading (NBT, regions, world info) lives in the sibling
[`grimmcraft-world`](../grimmcraft-world) package, which builds on this one.

## Tasks

```sh
task fs:test        # run the tests
task fs:lint        # ruff
task fs:typecheck   # mypy
```
