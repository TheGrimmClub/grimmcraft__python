"""Auto-generated from PrismarineJS/minecraft-data `recipes.json`.

Minecraft Java Edition 1.21.11 — 886 craftable result items.
Bundled source asset: data/1.21.11/recipes.json (loaded lazily via importlib.resources).

`Recipe.result_item` is the `Item` enum member for the crafted item (or the raw
int id if that member is absent in this build); `.shape` is a tuple of rows for
shaped recipes (cells are `Item`/int/`None`) and `.ingredients` a flat tuple for
shapeless ones.  NOTE: numeric item ids are stable within a version but change
between versions.
Do not edit by hand; regenerate with _generate/advanced_recipe.py."""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import cache, lru_cache
from importlib.resources import files
from pathlib import Path
from typing import Union

_DATA = "data/1.21.11/recipes.json"
_HERE = Path(__file__).parent

try:
    from .item import Item
except Exception:  # pragma: no cover - Item enum optional
    Item = None


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


@cache
def recipes_for(item) -> list[Recipe]:
    """All recipes producing `item` (an `Item` member, int id, or id string)."""
    key = str(item.value if hasattr(item, "value") else item)
    return [_parse(r) for r in _raw().get(key, [])]


def all_recipes() -> dict[int, list[Recipe]]:
    """Every recipe, keyed by result item int id."""
    return {int(k): [_parse(r) for r in v] for k, v in _raw().items()}
