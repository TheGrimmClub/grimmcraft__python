"""Auto-generated from PrismarineJS/minecraft-data `language.json`.

Minecraft Java Edition 1.21.11 — 7767 en_us translation keys.
Bundled source asset: data/1.21.11/language.json (loaded lazily via importlib.resources).

`translate(key, default=None)` maps a translation key (e.g. "block.minecraft.stone")
to its English text; `all_keys()` returns every available key.
Do not edit by hand; regenerate with _generate/advanced_language.py."""

from __future__ import annotations

import json
from functools import lru_cache
from importlib.resources import files
from pathlib import Path

_DATA = "data/1.21.11/language.json"
_HERE = Path(__file__).parent


def _open_data():
    try:
        return files(__package__).joinpath(_DATA).open("r", encoding="utf-8")
    except (ModuleNotFoundError, TypeError, FileNotFoundError):
        return (_HERE / _DATA).open("r", encoding="utf-8")


@lru_cache(maxsize=1)
def _raw() -> dict:
    with _open_data() as fh:
        return json.load(fh)


def translate(key: str, default: str | None = None) -> str | None:
    """English text for a translation key, or `default` if it is not present."""
    return _raw().get(key, default)


def all_keys():
    """A view of every available translation key."""
    return _raw().keys()
