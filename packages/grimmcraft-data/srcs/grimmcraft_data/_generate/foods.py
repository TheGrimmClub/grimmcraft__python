#!/usr/bin/env python3
"""Generate a Python Enum of all vanilla Minecraft (Java Edition) food types.

Source of truth: PrismarineJS/minecraft-data `foods.json` (one file per version).
This downloads the authoritative list and writes `food.py` into the package
directory (one level up from this script), containing a `Food(Enum)` whose
members' .value is the integer registry id, with the .display_name, .food_points, .saturation, .stack_size attributes attached as attributes.

Usage:
    python _generate/foods.py               # latest available version
    python _generate/foods.py 1.21          # a specific version
    python _generate/foods.py --list        # print available versions
"""

import json
import keyword
import sys
import urllib.request
from pathlib import Path

BASE = "https://raw.githubusercontent.com/PrismarineJS/minecraft-data/master/data"
PATHS_URL = f"{BASE}/dataPaths.json"
OUTPUT_PATH = Path(__file__).parent.parent / "food.py"
TYPE_KEY = "foods"


def fetch_json(url):
    with urllib.request.urlopen(url, timeout=30) as r:
        return json.load(r)


def available_versions():
    """Versions (in file order, oldest -> newest) that ship a foods.json."""
    paths = fetch_json(PATHS_URL)["pc"]
    return [v for v, entry in paths.items() if TYPE_KEY in entry]


def data_url(version):
    paths = fetch_json(PATHS_URL)["pc"]
    rel = paths[version][TYPE_KEY]  # directory, e.g. "pc/1.21.11"
    return f"{BASE}/{rel}/{TYPE_KEY}.json"


def member_name(full_id):
    """Turn 'minecraft:oak_log' into a valid, unique-ish enum member name."""
    name = full_id.split(":", 1)[-1].upper()
    if not name[:1].isalpha() and name[:1] != "_":
        name = "N_" + name          # names can't start with a digit
    if keyword.iskeyword(name.lower()):
        name += "_"
    return name


def py_str(value):
    """Render a Python literal (or None) for the generated source.

    json.dumps escapes apostrophes/quotes safely and handles ints, floats and
    strings uniformly; None becomes the literal None (not JSON null).
    """
    return "None" if value is None else json.dumps(value)


def build_enum(entries, version):
    seen = set()
    lines = [
        '"""Auto-generated from PrismarineJS/minecraft-data.',
        f"Minecraft Java Edition {version} — {len(entries)} food types.",
        "",
        "Each member's .value is the integer registry id for this version;",
        ".string_id is the namespaced id (e.g. 'minecraft:apple').",
        ".display_name is the human label.",
        ".food_points is hunger restored.",
        ".saturation is saturation restored.",
        ".stack_size is the max stack.",
        "NOTE: numeric ids are stable within a version but change between",
        "versions (Java has no permanent numeric ids since 1.13).",
        'Do not edit by hand; regenerate with _generate/foods.py."""',
        "",
        "from enum import Enum",
        "",
        "",
        "class Food(Enum):",
        "    def __new__(cls, num_id, string_id, display_name, food_points, saturation, stack_size):",
        "        obj = object.__new__(cls)",
        "        obj._value_ = num_id",
        "        obj.string_id = string_id",
        "        obj.display_name = display_name",
        "        obj.food_points = food_points",
        "        obj.saturation = saturation",
        "        obj.stack_size = stack_size",
        "        return obj",
        "",
    ]
    for e in entries:
        full_id = e["name"] if ":" in e["name"] else f"minecraft:{e['name']}"
        name = member_name(full_id)
        while name in seen:            # guard against collisions
            name += "_"
        seen.add(name)
        display_name = py_str(e.get("displayName"))
        food_points = py_str(e.get("foodPoints"))
        saturation = py_str(e.get("saturation"))
        stack_size = py_str(e.get("stackSize"))
        lines.append(f'    {name} = ({e["id"]}, {py_str(full_id)}, {display_name}, {food_points}, {saturation}, {stack_size})')
    lines.append("")
    return "\n".join(lines)


def main():
    args = list(sys.argv[1:])
    if "--list" in args:
        print("\n".join(available_versions()))
        return

    version = args[0] if args else available_versions()[-1]
    print(f"Fetching food list for Java Edition {version} ...")
    entries = fetch_json(data_url(version))
    code = build_enum(entries, version)

    OUTPUT_PATH.write_text(code)
    print(f"Wrote {OUTPUT_PATH} with {len(entries)} food types. Example: Food.APPLE")


if __name__ == "__main__":
    main()
