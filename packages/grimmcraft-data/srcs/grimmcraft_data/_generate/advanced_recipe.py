#!/usr/bin/env python3
"""Bundle Minecraft (Java Edition) crafting recipes and emit a typed accessor.

Source of truth: PrismarineJS/minecraft-data `recipes.json` (one file per
version) -- a top-level object keyed by result item id whose values are lists of
recipes.  Each recipe is either shapeless (`ingredients`) or shaped (`inShape`),
plus a `result` ({id, count} on modern versions, a bare id on old ones).

This downloads the file, saves it verbatim under `../data/{version}/recipes.json`
(the shipped asset) and generates `../recipe.py` with frozen dataclasses and
lazy, cached lookups that resolve ids to `Item` enum members when available.

Usage:
    python _generate/advanced_recipe.py            # latest available version
    python _generate/advanced_recipe.py 1.21       # a specific version
    python _generate/advanced_recipe.py --list     # print available versions
"""

import json
import sys
import urllib.request
from pathlib import Path

BASE = "https://raw.githubusercontent.com/PrismarineJS/minecraft-data/master/data"
PATHS_URL = f"{BASE}/dataPaths.json"
TYPE_KEY = "recipes"
PKG_DIR = Path(__file__).parent.parent
OUTPUT_PATH = PKG_DIR / "recipe.py"
DATA_DIR = PKG_DIR / "data"


def fetch_text(url):
    with urllib.request.urlopen(url, timeout=30) as r:
        return r.read().decode("utf-8")


def available_versions():
    paths = json.loads(fetch_text(PATHS_URL))["pc"]
    return [v for v, entry in paths.items() if TYPE_KEY in entry]


def data_url(version):
    rel = json.loads(fetch_text(PATHS_URL))["pc"][version][TYPE_KEY]  # a directory
    return f"{BASE}/{rel}/{TYPE_KEY}.json"


def save_bundle(version, raw_text):
    dest = DATA_DIR / version / f"{TYPE_KEY}.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(raw_text, encoding="utf-8")  # verbatim
    return dest


def build_module(version, data_rel, count):
    header = f'''"""Auto-generated from PrismarineJS/minecraft-data `recipes.json`.

Minecraft Java Edition {version} — {count} craftable result items.
Bundled source asset: {data_rel} (loaded lazily via importlib.resources).

`Recipe.result_item` is the `Item` enum member for the crafted item (or the raw
int id if that member is absent in this build); `.shape` is a tuple of rows for
shaped recipes (cells are `Item`/int/`None`) and `.ingredients` a flat tuple for
shapeless ones.  NOTE: numeric item ids are stable within a version but change
between versions.
Do not edit by hand; regenerate with _generate/advanced_recipe.py."""

from __future__ import annotations

from grimmclub_standardlib import SystemPath as Path
from grimmclub_standardlib import dataclass, files, json, lru_cache
from typing import Optional, Union

_DATA = {json.dumps(data_rel)}
_HERE = Path(__file__).parent

try:
    from .item import Item
except Exception:  # pragma: no cover - Item enum optional
    Item = None
'''
    body = r'''

Ingredient = Union["Item", int, None]


@dataclass(frozen=True, slots=True)
class Recipe:
    """A single crafting recipe for one result item."""

    result_item: object          # Item member, or raw int id
    result_count: int
    shape: tuple | None        # tuple[tuple[Ingredient, ...], ...] if shaped
    ingredients: tuple | None  # tuple[Ingredient, ...] if shapeless

    @property
    def is_shaped(self) -> bool:
        return self.shape is not None


def _resolve_item(num_id):
    if Item is None or num_id is None:
        return num_id
    try:
        return Item(num_id)
    except ValueError:
        return num_id


def _norm_cell(cell):
    if cell is None:
        return None
    if isinstance(cell, dict):  # older shape: {id, metadata}
        return _resolve_item(cell.get("id"))
    return _resolve_item(cell)


def _open_data():
    try:
        return files(__package__).joinpath(_DATA).open("r", encoding="utf-8")
    except (ModuleNotFoundError, TypeError, FileNotFoundError):
        return (_HERE / _DATA).open("r", encoding="utf-8")


@lru_cache(maxsize=1)
def _raw() -> dict:
    with _open_data() as fh:
        return json.load(fh)


def _parse(rec) -> Recipe:
    result = rec.get("result")
    if isinstance(result, dict):
        rid, count = result.get("id"), result.get("count", 1)
    else:  # bare id (older versions)
        rid, count = result, 1
    shape = None
    ingredients = None
    if rec.get("inShape") is not None:
        shape = tuple(tuple(_norm_cell(c) for c in row) for row in rec["inShape"])
    if rec.get("ingredients") is not None:
        ingredients = tuple(_norm_cell(c) for c in rec["ingredients"])
    return Recipe(_resolve_item(rid), count or 1, shape, ingredients)


@lru_cache(maxsize=None)
def recipes_for(item) -> list[Recipe]:
    """All recipes producing `item` (an `Item` member, int id, or id string)."""
    key = str(item.value if hasattr(item, "value") else item)
    return [_parse(r) for r in _raw().get(key, [])]


def all_recipes() -> dict[int, list[Recipe]]:
    """Every recipe, keyed by result item int id."""
    return {int(k): [_parse(r) for r in v] for k, v in _raw().items()}
'''
    return header + body


def main():
    args = list(sys.argv[1:])
    if "--list" in args:
        print("\n".join(available_versions()))
        return
    positional = [a for a in args if not a.startswith("-")]
    version = positional[0] if positional else available_versions()[-1]

    print(f"Fetching recipes for Java Edition {version} ...")
    raw = fetch_text(data_url(version))
    obj = json.loads(raw)
    dest = save_bundle(version, raw)
    code = build_module(version, f"data/{version}/{TYPE_KEY}.json", len(obj))
    OUTPUT_PATH.write_text(code)
    print(f"Bundled {dest}")
    print(f"Wrote {OUTPUT_PATH} ({len(obj)} result items). Example: recipes_for(Item.CHEST)")


if __name__ == "__main__":
    main()
