"""Auto-generated from PrismarineJS/minecraft-data `blockCollisionShapes.json`.

Minecraft Java Edition 1.21.11 — 1166 blocks, 5128 distinct shapes.
Bundled source asset: data/1.21.11/blockCollisionShapes.json (loaded lazily via importlib.resources).

`collision_boxes(block, state_index=0)` returns the list of `AABB`s for a block
state.  Coordinates are in block units (0..1 per axis, may exceed for tall
blocks like fences).  NOTE: shape ids are internal to this dataset/version.
Do not edit by hand; regenerate with _generate/advanced_collision_shape.py."""

from __future__ import annotations

from grimmclub_standardlib import SystemPath as Path
from grimmclub_standardlib import dataclass, files, json, lru_cache

_DATA = "data/1.21.11/blockCollisionShapes.json"
_HERE = Path(__file__).parent


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
