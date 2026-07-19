#!/usr/bin/env python3
"""Emit a frozen-dataclass registry of Minecraft (Java Edition) entity attributes.

Source of truth: PrismarineJS/minecraft-data `attributes.json` -- a small list of
`{name, resource, min, max, default}` records.  Because it is tiny it is inlined
directly into the generated `../attribute.py` (no bundled JSON asset needed).

Provides `ATTRIBUTES` keyed by resource name (e.g. "minecraft:generic.max_health")
and an `attribute(resource)` helper.

Usage:
    python _generate/advanced_attribute.py            # latest version
    python _generate/advanced_attribute.py 1.21       # a specific version
    python _generate/advanced_attribute.py --list     # available versions
"""

import json
import sys
import urllib.request
from pathlib import Path

BASE = "https://raw.githubusercontent.com/PrismarineJS/minecraft-data/master/data"
PATHS_URL = f"{BASE}/dataPaths.json"
TYPE_KEY = "attributes"
PKG_DIR = Path(__file__).parent.parent
OUTPUT_PATH = PKG_DIR / "attribute.py"


def fetch_text(url):
    with urllib.request.urlopen(url, timeout=30) as r:
        return r.read().decode("utf-8")


def available_versions():
    paths = json.loads(fetch_text(PATHS_URL))["pc"]
    return [v for v, entry in paths.items() if TYPE_KEY in entry]


def data_url(version):
    rel = json.loads(fetch_text(PATHS_URL))["pc"][version][TYPE_KEY]  # a directory
    return f"{BASE}/{rel}/{TYPE_KEY}.json"


def py(value):
    """Render a Python literal (None/number/str) for the generated source."""
    return "None" if value is None else json.dumps(value)


def build_module(version, records):
    lines = [
        '"""Auto-generated from PrismarineJS/minecraft-data `attributes.json`.',
        "",
        f"Minecraft Java Edition {version} — {len(records)} entity attributes.",
        "",
        "`ATTRIBUTES` is keyed by resource name; each value is a frozen `Attribute`",
        "with its default and clamped min/max.  NOTE: resource names and ranges are",
        "stable within a version but may change between versions.",
        'Do not edit by hand; regenerate with _generate/advanced_attribute.py."""',
        "",
        "from __future__ import annotations",
        "",
        "from dataclasses import dataclass",
        "",
        "",
        "@dataclass(frozen=True, slots=True)",
        "class Attribute:",
        '    """A single entity attribute and its allowed value range."""',
        "",
        "    name: str",
        "    resource: str",
        "    default: float | None",
        "    min: float | None",
        "    max: float | None",
        "",
        "",
        "ATTRIBUTES: dict[str, Attribute] = {",
    ]
    for r in records:
        resource = r.get("resource") or r.get("name")
        lines.append(
            f"    {py(resource)}: Attribute("
            f"{py(r.get('name'))}, {py(resource)}, "
            f"{py(r.get('default'))}, {py(r.get('min'))}, {py(r.get('max'))}),"
        )
    lines += [
        "}",
        "",
        "",
        "def attribute(resource: str) -> Attribute | None:",
        '    """Look up an attribute by its resource name."""',
        "    return ATTRIBUTES.get(resource)",
        "",
    ]
    return "\n".join(lines)


def main():
    args = list(sys.argv[1:])
    if "--list" in args:
        print("\n".join(available_versions()))
        return
    positional = [a for a in args if not a.startswith("-")]
    version = positional[0] if positional else available_versions()[-1]

    print(f"Fetching attributes for Java Edition {version} ...")
    records = json.loads(fetch_text(data_url(version)))
    code = build_module(version, records)
    OUTPUT_PATH.write_text(code)
    print(f"Wrote {OUTPUT_PATH} ({len(records)} attributes, inlined).")


if __name__ == "__main__":
    main()
