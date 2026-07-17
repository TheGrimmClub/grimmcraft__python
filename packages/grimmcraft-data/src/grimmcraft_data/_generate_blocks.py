#!/usr/bin/env python3
"""Generate a Python Enum of all vanilla Minecraft (Java Edition) block types.

Source of truth: PrismarineJS/minecraft-data `blocks.json` (one file per version).
This downloads the authoritative list and writes `minecraft_blocks.py` containing a
`Block(str, Enum)` whose members are UPPER_SNAKE names and whose values are the
namespaced string IDs (e.g. Block.OAK_LOG == "minecraft:oak_log").

Usage:
    python generate_block_enum.py               # latest available version
    python generate_block_enum.py 1.21          # a specific version
    python generate_block_enum.py --list        # print available versions
"""

import json
import keyword
import sys
import urllib.request

from pathlib import Path

BASE = "https://raw.githubusercontent.com/PrismarineJS/minecraft-data/master/data"
PATHS_URL = f"{BASE}/dataPaths.json"
OUTPUT_PATH = Path(__file__).parent / "blocks.py"

def fetch_json(url):
    with urllib.request.urlopen(url, timeout=30) as r:
        return json.load(r)


def available_versions():
    """Versions (in file order, oldest -> newest) that ship a blocks.json."""
    paths = fetch_json(PATHS_URL)["pc"]
    return [v for v, entry in paths.items() if "blocks" in entry]


def blocks_url(version):
    paths = fetch_json(PATHS_URL)["pc"]
    rel = paths[version]["blocks"]  # directory, e.g. "pc/1.21.11"
    return f"{BASE}/{rel}/blocks.json"


def member_name(block_id):
    """Turn 'minecraft:oak_log' into a valid, unique-ish enum member name."""
    name = block_id.split(":", 1)[-1].upper()
    if not name[:1].isalpha() and name[:1] != "_":
        name = "N_" + name          # names can't start with a digit
    if keyword.iskeyword(name.lower()):
        name += "_"
    return name


def build_enum(blocks, version):
    seen = {}
    lines = [
        '"""Auto-generated from PrismarineJS/minecraft-data.',
        f"Minecraft Java Edition {version} — {len(blocks)} block types.",
        'Do not edit by hand; regenerate with generate_block_enum.py."""',
        "",
        "from enum import Enum",
        "",
        "",
        "class Block(str, Enum):",
    ]
    for b in blocks:
        full_id = b["name"] if ":" in b["name"] else f"minecraft:{b['name']}"
        name = member_name(full_id)
        while name in seen:            # guard against collisions
            name += "_"
        seen[name] = full_id
        lines.append(f'    {name} = "{full_id}"')
    lines.append("")
    return "\n".join(lines)


def main():
    args = [a for a in sys.argv[1:]]
    if "--list" in args:
        print("\n".join(available_versions()))
        return

    version = args[0] if args else available_versions()[-1]
    print(f"Fetching block list for Java Edition {version} ...")
    blocks = fetch_json(blocks_url(version))
    code = build_enum(blocks, version)
    code += '''
    def __str__(self) -> str:
        """compact string representation."""
        return super().__str__().replace("minecraft:", "")

    def to_int(self) -> int:
        """get integer value."""
        return int(self.value.split(":")[1])
    '''

    with open(OUTPUT_PATH, "w") as f:
        f.write(code)
    print(f"Wrote {OUTPUT_PATH} with {len(blocks)} blocks. Example: Block.OAK_LOG")


if __name__ == "__main__":
    main()
