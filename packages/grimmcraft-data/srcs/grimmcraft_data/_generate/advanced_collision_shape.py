#!/usr/bin/env python3
"""Bundle Minecraft (Java Edition) block collision shapes and emit an accessor.

Source of truth: PrismarineJS/minecraft-data `blockCollisionShapes.json` --
`{blocks: {name: shapeId | [shapeId, ...]}, shapes: {id: [[x0,y0,z0,x1,y1,z1], ...]}}`.
A block maps to one shape id (all states share it) or a list (one id per state).

This downloads the file, saves it verbatim under
`../data/{version}/blockCollisionShapes.json`, and generates
`../collision_shape.py` which dereferences a block (per-state) to its AABBs.

Usage:
    python _generate/advanced_collision_shape.py            # latest version
    python _generate/advanced_collision_shape.py 1.21       # a specific version
    python _generate/advanced_collision_shape.py --list     # available versions
"""

import json
import sys
import urllib.request
from pathlib import Path

BASE = "https://raw.githubusercontent.com/PrismarineJS/minecraft-data/master/data"
PATHS_URL = f"{BASE}/dataPaths.json"
TYPE_KEY = "blockCollisionShapes"
PKG_DIR = Path(__file__).parent.parent
OUTPUT_PATH = PKG_DIR / "collision_shape.py"
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


def build_module(version, data_rel, n_blocks, n_shapes):
    header = f'''"""Auto-generated from PrismarineJS/minecraft-data `blockCollisionShapes.json`.

Minecraft Java Edition {version} — {n_blocks} blocks, {n_shapes} distinct shapes.
Bundled source asset: {data_rel} (loaded lazily via importlib.resources).

`collision_boxes(block, state_index=0)` returns the list of `AABB`s for a block
state.  Coordinates are in block units (0..1 per axis, may exceed for tall
blocks like fences).  NOTE: shape ids are internal to this dataset/version.
Do not edit by hand; regenerate with _generate/advanced_collision_shape.py."""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from importlib.resources import files
from pathlib import Path

_DATA = {json.dumps(data_rel)}
_HERE = Path(__file__).parent
'''
    body = r'''

@dataclass(frozen=True, slots=True)
class AABB:
    """An axis-aligned bounding box in block-space (min corner .. max corner)."""

    min_x: float
    min_y: float
    min_z: float
    max_x: float
    max_y: float
    max_z: float


def _name(x) -> str:
    """Normalise a Block enum member or id string to a bare (un-namespaced) name."""
    s = getattr(x, "string_id", x)
    return str(s).split(":", 1)[-1]


def _open_data():
    try:
        return files(__package__).joinpath(_DATA).open("r", encoding="utf-8")
    except (ModuleNotFoundError, TypeError, FileNotFoundError):
        return (_HERE / _DATA).open("r", encoding="utf-8")


@lru_cache(maxsize=1)
def _raw() -> dict:
    with _open_data() as fh:
        return json.load(fh)


def collision_boxes(block, state_index: int = 0) -> list[AABB]:
    """AABBs for a block state (an `Block` member or bare/namespaced id).

    `block` may map to a single shape (all states) or a per-state list; unknown
    blocks yield an empty list.
    """
    data = _raw()
    entry = data["blocks"].get(_name(block))
    if entry is None:
        return []
    if isinstance(entry, list):
        if not entry:
            return []
        idx = state_index if 0 <= state_index < len(entry) else 0
        shape_id = entry[idx]
    else:
        shape_id = entry
    return [AABB(*box) for box in data["shapes"].get(str(shape_id), [])]


def shape_count(block) -> int:
    """Number of distinct collision states recorded for a block (1 if scalar)."""
    entry = _raw()["blocks"].get(_name(block))
    if entry is None:
        return 0
    return len(entry) if isinstance(entry, list) else 1
'''
    return header + body


def main():
    args = list(sys.argv[1:])
    if "--list" in args:
        print("\n".join(available_versions()))
        return
    positional = [a for a in args if not a.startswith("-")]
    version = positional[0] if positional else available_versions()[-1]

    print(f"Fetching collision shapes for Java Edition {version} ...")
    raw = fetch_text(data_url(version))
    obj = json.loads(raw)
    dest = save_bundle(version, raw)
    code = build_module(
        version,
        f"data/{version}/{TYPE_KEY}.json",
        len(obj.get("blocks", {})),
        len(obj.get("shapes", {})),
    )
    OUTPUT_PATH.write_text(code)
    print(f"Bundled {dest}")
    print(f"Wrote {OUTPUT_PATH} ({len(obj.get('blocks', {}))} blocks).")


if __name__ == "__main__":
    main()
