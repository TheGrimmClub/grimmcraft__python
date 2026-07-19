#!/usr/bin/env python3
"""Bundle the Minecraft (Java Edition) en_us translation table and emit an accessor.

Source of truth: PrismarineJS/minecraft-data `language.json` -- a large flat
`{translation_key: text}` map.  Because it is large it is shipped as a bundled
JSON asset (not inlined) and read lazily.

Generates `../language.py` with `translate(key, default=None)` and `all_keys()`.

Usage:
    python _generate/advanced_language.py            # latest version
    python _generate/advanced_language.py 1.21       # a specific version
    python _generate/advanced_language.py --list     # available versions
"""

import urllib.request

from grimmclub_standardlib import SystemPath, json, sys

BASE = "https://raw.githubusercontent.com/PrismarineJS/minecraft-data/master/data"
PATHS_URL = f"{BASE}/dataPaths.json"
TYPE_KEY = "language"
PKG_DIR = SystemPath(__file__).parent.parent
OUTPUT_PATH = PKG_DIR / "language.py"
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
    header = f'''"""Auto-generated from PrismarineJS/minecraft-data `language.json`.

Minecraft Java Edition {version} — {count} en_us translation keys.
Bundled source asset: {data_rel} (loaded lazily via importlib.resources).

`translate(key, default=None)` maps a translation key (e.g. "block.minecraft.stone")
to its English text; `all_keys()` returns every available key.
Do not edit by hand; regenerate with _generate/advanced_language.py."""

from __future__ import annotations

from grimmclub_standardlib import json
from grimmclub_standardlib import lru_cache
from grimmclub_standardlib import files
from grimmclub_standardlib import SystemPath

_DATA = {json.dumps(data_rel)}
_HERE = SystemPath(__file__).parent
'''
    body = r'''

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
'''
    return header + body


def main():
    args = list(sys.argv[1:])
    if "--list" in args:
        print("\n".join(available_versions()))
        return
    positional = [a for a in args if not a.startswith("-")]
    version = positional[0] if positional else available_versions()[-1]

    print(f"Fetching language table for Java Edition {version} ...")
    raw = fetch_text(data_url(version))
    obj = json.loads(raw)
    dest = save_bundle(version, raw)
    code = build_module(version, f"data/{version}/{TYPE_KEY}.json", len(obj))
    OUTPUT_PATH.write_text(code)
    print(f"Bundled {dest}")
    print(f"Wrote {OUTPUT_PATH} ({len(obj)} keys).")


if __name__ == "__main__":
    main()
