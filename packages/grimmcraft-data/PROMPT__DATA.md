# Task: generate `_generate_{type}.py` data-enum generators
> [x] execute PROMPT__ADVANCED.md

Create one generator script per registry type listed below, in the current
directory (the package you were invoked from, e.g.
`packages/grimmcraft-data/src/grimmcraft_data/`). Each script downloads the
authoritative list from PrismarineJS/minecraft-data and writes a Python `Enum`
module next to itself.

## Files to create

For each `{type}` below, create `_generate_{type}.py` that writes `{type}.py`:

- `block`   → from `blocks.json`   → `class Block`   (attrs: string_id, default_state)
- `item`    → from `items.json`    → `class Item`    (attrs: string_id, display_name, stack_size)
- `entity`  → from `entities.json` → `class Entity`  (attrs: string_id, display_name, type, category)
- `biome`   → from `biomes.json`   → `class Biome`   (attrs: string_id, display_name, category, dimension)
- `effect`  → from `effects.json`  → `class Effect`  (attrs: string_id, display_name, type)
- `enchantment` → from `enchantments.json` → `class Enchantment` (attrs: string_id, display_name, max_level, category)
- `food`    → from `foods.json`    → `class Food`    (attrs: string_id, display_name, food_points, saturation, stack_size)
- `particle`→ from `particles.json`→ `class Particle`(attrs: string_id)
- `instrument` → from `instruments.json` → `class Instrument` (attrs: string_id)

(If a listed attribute is missing from a given version's JSON, emit `None` for it
rather than failing.)

## Hard requirements (match exactly)

1. **Source resolution.** Base URL:
   `https://raw.githubusercontent.com/PrismarineJS/minecraft-data/master/data`.
   Read `dataPaths.json`; `paths["pc"][version][{type_key}]` is a **directory**
   (e.g. `"pc/1.21.11"`). The file URL is `{BASE}/{rel}/{type_key}.json`
   (note the `/` — do NOT append `.json` to the directory).
   `{type_key}` is the plural JSON name (`blocks`, `items`, `entities`, `biomes`,
   `effects`, `enchantments`, `foods`, `particles`, `instruments`).

2. **Output path.** Use exactly:
   `OUTPUT_PATH = Path(__file__).parent / "{type}.py"` and write with
   `OUTPUT_PATH.write_text(code)`. No `out` variable, no relative CWD path.

3. **Enum value = integer registry id.** Use the `__new__` pattern so
   `Member.value` is the int `id`, with the other fields as attributes:
   ```python
   class Block(Enum):
       def __new__(cls, num_id, string_id, default_state):
           obj = object.__new__(cls)
           obj._value_ = num_id
           obj.string_id = string_id
           obj.default_state = default_state
           return obj
   ```
   This keeps `Block(17)` reverse-lookup working. `blocks` has no `stackSize`;
   for `block`, `default_state = entry.get("defaultState", entry.get("minStateId"))`.

4. **Member names.** `member_name(id)` = the part after `:` uppercased; prefix
   `N_` if it starts with a non-letter; append `_` if it collides with a Python
   keyword; append `_` again to resolve duplicate member names.

5. **String literals in generated code.** Render text fields (display names etc.)
   with `json.dumps(value)`, and `None` when absent — never raw f-string
   interpolation, so apostrophes/quotes are escaped safely.

6. **CLI.** `python _generate_{type}.py` uses the latest available version;
   `python _generate_{type}.py 1.21` pins a version; `--list` prints all versions
   that ship that `{type_key}.json`. "Latest" = last entry of that filtered list.

7. **Generated file header.** A module docstring noting it's auto-generated from
   PrismarineJS/minecraft-data, the version, the count, what `.value` and each
   attribute mean, and the caveat that numeric ids are stable within a version
   but change between versions (Java has no permanent numeric ids since 1.13).

8. Standard library only (`json`, `keyword`, `sys`, `urllib.request`, `pathlib`).
   30s timeout on requests.

## Reference skeleton (adapt per type)

```python
#!/usr/bin/env python3
"""Generate a Python Enum of all vanilla Minecraft (Java Edition) {type} types."""
import json, keyword, sys, urllib.request
from pathlib import Path

BASE = "https://raw.githubusercontent.com/PrismarineJS/minecraft-data/master/data"
PATHS_URL = f"{BASE}/dataPaths.json"
OUTPUT_PATH = Path(__file__).parent / "{type}.py"
TYPE_KEY = "{type_key}"   # e.g. "blocks"

def fetch_json(url):
    with urllib.request.urlopen(url, timeout=30) as r:
        return json.load(r)

def available_versions():
    paths = fetch_json(PATHS_URL)["pc"]
    return [v for v, e in paths.items() if TYPE_KEY in e]

def data_url(version):
    rel = fetch_json(PATHS_URL)["pc"][version][TYPE_KEY]
    return f"{BASE}/{rel}/{TYPE_KEY}.json"

def member_name(full_id):
    name = full_id.split(":", 1)[-1].upper()
    if not name[:1].isalpha() and name[:1] != "_":
        name = "N_" + name
    if keyword.iskeyword(name.lower()):
        name += "_"
    return name

def py_str(v):
    return "None" if v is None else json.dumps(v)

# build_enum(...) emits the class with the __new__ pattern and one member per entry.
# main(): handle --list, pick version, fetch, build, OUTPUT_PATH.write_text(code).
```

## Also

- After creating the scripts, run each once and confirm the generated `{type}.py`
  imports cleanly (`python -c "import {type}"`) and a spot-checked member has the
  expected `.value` and attributes.
- Keep all nine scripts consistent — they should differ only in TYPE_KEY, the
  class name, and which attributes are pulled from each entry.
```
