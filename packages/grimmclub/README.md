# grimmclub

A curated, teaching-friendly facade over the Python **standard library**. Import
the everyday "batteries" from one place — same names, same APIs — plus a few
helpers that make it easy to show students what their code is doing.

```python
from grimmclub import Path, StrEnum, dataclass, field   # common leaf names
from grimmclub import json, math                          # whole modules
from grimmclub import log, debug, banner                  # teaching helpers

@dataclass
class Player:
    name: str
    home: Path

banner("Demo")
log("hello", 42)          # -> [grimmclub] hello 42   (on stderr)
debug("only shown when GRIMMCLUB_DEBUG=1 or set_debug(True)")
print(json.dumps({"ok": True}))
```

## Why

`grimmclub` keeps the stdlib names and APIs, but gives **one place** to add extra
help, logging or debug output for a class — change it here, every script benefits.

- **Leaf names** are re-exported directly (`Path`, `dataclass`, `StrEnum`, `Any`,
  `datetime`, `Counter`, …) because that's how they're normally imported.
- **Whole modules** are re-exported for things whose members would collide if
  flattened (`json`, `os`, `math`, `random`, `itertools`, `textwrap`, `sys`) —
  use them as `json.dumps(...)`, `os.getcwd()`.

A flat facade can't expose *all* of the stdlib without name clashes, so this is a
curated set. Add more in `srcs/grimmclub/__init__.py` as your students need it.

## Helpers

| Helper | What it does |
|--------|--------------|
| `log(*values)` | Print to stderr, prefixed `[grimmclub]`. |
| `debug(*values)` | Same, but only when `GRIMMCLUB_DEBUG=1` or `set_debug(True)`. |
| `set_debug(bool)` / `debug_enabled()` | Toggle / query debug output. |
| `banner(title)` | A centred titled separator line for structuring output. |
