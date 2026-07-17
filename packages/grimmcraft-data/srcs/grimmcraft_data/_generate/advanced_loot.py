#!/usr/bin/env python3
"""Bundle Minecraft (Java Edition) block/entity loot tables and emit an accessor.

Source of truth: PrismarineJS/minecraft-data `blockLoot.json` and
`entityLoot.json` (one pair per version) -- lists of
`{block|entity, drops: [{item, dropChance, stackSizeRange, ...}]}` whose ids are
un-namespaced (e.g. "acacia_button").

This downloads both files, saves them verbatim under `../data/{version}/`, and
generates `../loot.py` with frozen dataclasses and lazy, cached lookups keyed by
string id, resolving drop items to `Item` enum members when available.

Usage:
    python _generate/advanced_loot.py            # latest available version
    python _generate/advanced_loot.py 1.21       # a specific version
    python _generate/advanced_loot.py --list     # print available versions
"""

import json
import sys
import urllib.request
from pathlib import Path

BASE = "https://raw.githubusercontent.com/PrismarineJS/minecraft-data/master/data"
PATHS_URL = f"{BASE}/dataPaths.json"
BLOCK_KEY = "blockLoot"
ENTITY_KEY = "entityLoot"
PKG_DIR = Path(__file__).parent.parent
OUTPUT_PATH = PKG_DIR / "loot.py"
DATA_DIR = PKG_DIR / "data"


def fetch_text(url):
    with urllib.request.urlopen(url, timeout=30) as r:
        return r.read().decode("utf-8")


def available_versions(key):
    paths = json.loads(fetch_text(PATHS_URL))["pc"]
    return [v for v, entry in paths.items() if key in entry]


def data_url(version, key):
    rel = json.loads(fetch_text(PATHS_URL))["pc"][version][key]  # a directory
    return f"{BASE}/{rel}/{key}.json"


def save_bundle(version, key, raw_text):
    dest = DATA_DIR / version / f"{key}.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(raw_text, encoding="utf-8")  # verbatim
    return dest


def build_module(version, block_rel, entity_rel, n_block, n_entity):
    header = f'''"""Auto-generated from PrismarineJS/minecraft-data loot tables.

Minecraft Java Edition {version} — {n_block} block and {n_entity} entity loot tables.
Bundled source assets: {block_rel}, {entity_rel} (loaded lazily).

`Drop.item` is the `Item` enum member for the dropped item (or its bare string
id if that member is absent); `.drop_chance` is the base chance and
`.stack_min`/`.stack_max` the stack-size range.  `block_loot()` / `entity_loot()`
are keyed by bare string id (e.g. "stone", "zombie") and also accept enum
members.
Do not edit by hand; regenerate with _generate/advanced_loot.py."""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from importlib.resources import files
from pathlib import Path
from typing import Optional

_BLOCK_DATA = {json.dumps(block_rel)}
_ENTITY_DATA = {json.dumps(entity_rel)}
_HERE = Path(__file__).parent

try:
    from .item import Item
except Exception:  # pragma: no cover - Item enum optional
    Item = None
'''
    body = r'''

@dataclass(frozen=True, slots=True)
class Drop:
    """A single possible drop within a loot table."""

    item: object                  # Item member, or bare string id
    drop_chance: Optional[float]
    stack_min: Optional[int]
    stack_max: Optional[int]
    silk_touch: Optional[bool]
    no_silk_touch: Optional[bool]
    player_kill: Optional[bool]
    block_age: Optional[int]


@dataclass(frozen=True, slots=True)
class LootTable:
    """The set of drops for one source block or entity."""

    source: str                   # bare string id
    drops: tuple[Drop, ...]


def _name(x) -> str:
    """Normalise an Item/enum member or id string to a bare (un-namespaced) name."""
    s = getattr(x, "string_id", x)
    return str(s).split(":", 1)[-1]


@lru_cache(maxsize=1)
def _item_by_name() -> dict:
    if Item is None:
        return {}
    return {m.string_id.split(":", 1)[-1]: m for m in Item}


def _resolve_item(name):
    return _item_by_name().get(name, name)


def _open(rel):
    try:
        return files(__package__).joinpath(rel).open("r", encoding="utf-8")
    except (ModuleNotFoundError, TypeError, FileNotFoundError):
        return (_HERE / rel).open("r", encoding="utf-8")


def _parse_drop(d) -> Drop:
    rng = d.get("stackSizeRange") or [None, None]
    lo = rng[0] if len(rng) > 0 else None
    hi = rng[1] if len(rng) > 1 else lo
    return Drop(
        item=_resolve_item(d.get("item")),
        drop_chance=d.get("dropChance"),
        stack_min=lo,
        stack_max=hi,
        silk_touch=d.get("silkTouch"),
        no_silk_touch=d.get("noSilkTouch"),
        player_kill=d.get("playerKill"),
        block_age=d.get("blockAge"),
    )


@lru_cache(maxsize=1)
def _tables(rel, source_field) -> dict:
    with _open(rel) as fh:
        rows = json.load(fh)
    out = {}
    for row in rows:
        src = row[source_field]
        out[src] = LootTable(src, tuple(_parse_drop(d) for d in row.get("drops", [])))
    return out


def block_loot(block) -> Optional[LootTable]:
    """Loot table for a block (an `Item`/`Block` member or bare/namespaced id)."""
    return _tables(_BLOCK_DATA, "block").get(_name(block))


def entity_loot(entity) -> Optional[LootTable]:
    """Loot table for an entity (an `Entity` member or bare/namespaced id)."""
    return _tables(_ENTITY_DATA, "entity").get(_name(entity))
'''
    return header + body


def main():
    args = list(sys.argv[1:])
    if "--list" in args:
        # versions shipping both files
        b = set(available_versions(BLOCK_KEY))
        versions = [v for v in available_versions(ENTITY_KEY) if v in b]
        print("\n".join(versions))
        return
    positional = [a for a in args if not a.startswith("-")]
    block_versions = available_versions(BLOCK_KEY)
    entity_versions = set(available_versions(ENTITY_KEY))
    both = [v for v in block_versions if v in entity_versions]
    version = positional[0] if positional else both[-1]

    print(f"Fetching loot tables for Java Edition {version} ...")
    block_raw = fetch_text(data_url(version, BLOCK_KEY))
    entity_raw = fetch_text(data_url(version, ENTITY_KEY))
    n_block = len(json.loads(block_raw))
    n_entity = len(json.loads(entity_raw))
    b_dest = save_bundle(version, BLOCK_KEY, block_raw)
    e_dest = save_bundle(version, ENTITY_KEY, entity_raw)
    code = build_module(
        version,
        f"data/{version}/{BLOCK_KEY}.json",
        f"data/{version}/{ENTITY_KEY}.json",
        n_block,
        n_entity,
    )
    OUTPUT_PATH.write_text(code)
    print(f"Bundled {b_dest}")
    print(f"Bundled {e_dest}")
    print(f"Wrote {OUTPUT_PATH} ({n_block} block / {n_entity} entity tables).")


if __name__ == "__main__":
    main()
