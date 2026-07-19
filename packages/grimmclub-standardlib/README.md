# grimmclub-standardlib

A curated facade over the Python standard library, plus the logging helpers and
the house vocabulary.

```python
from grimmclub_standardlib import Path, dataclass, StrEnum
from grimmclub_standardlib import json, math          # whole modules
from grimmclub_standardlib import log, banner, yes, no
```

## Where it sits

The **bottom** of the grimmclub stack. It has no dependencies and must keep
none, so that anything may rely on it:

```
grimmclub                 ← the front door trainees import
  ├── grimmclub-standardlib   (this package)
  └── grimmclub-filesystem    → also depends on this one
```

Trainees do not import this package directly — they import `grimmclub`, which
re-exports all of it. It exists separately so a *working* library such as
`grimmclub-filesystem` can share `yes`/`no` and `debug` without depending on the
whole teaching front door.

## What it provides

| | |
|---|---|
| Whole modules | `os`, `sys`, `json`, `math`, `random`, `itertools`, `textwrap` |
| Leaf names | `Path`, `dataclass`, `field`, `Enum`, `IntEnum`, `StrEnum`, `auto`, `Any`, `Optional`, `Protocol`, `date`, `datetime`, `time`, `timedelta`, `Counter`, `defaultdict`, `deque` |
| Teaching helpers | `log`, `debug`, `debug_enabled`, `set_debug`, `banner` |
| House vocabulary | `yes`, `no`, `true`, `false`, `on`, `off` |

Two names are genuinely **wrapped**, which is how the facade earns its keep:
`Path` and `json` are drop-in replacements that debug-log their I/O, so a lesson
can show what a program actually touches.
