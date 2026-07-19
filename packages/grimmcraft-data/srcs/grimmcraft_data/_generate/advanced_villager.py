#!/usr/bin/env python3
"""Emit the villager profession and workstation registries.

Usage:
    python _generate/advanced_villager.py
    python _generate/advanced_villager.py --version 1.21.11
    python _generate/advanced_villager.py --check      # verify, write nothing

# Where the data comes from, and why it is not one source

The profession *list* is Mojang's, read from the `language.json` this package
already ships: every profession has an `entity.minecraft.villager.<name>`
translation key, so the set is authoritative and versioned without needing a
server data report.

The profession-to-workstation *mapping* is not published in any Mojang data
file. `registries.json` lists the ids of `villager_profession` and
`point_of_interest_type` and nothing else -- each entry is `{"protocol_id": N}`,
with no blocks and no relation between the two registries. The mapping lives in
Minecraft's Java source (`VillagerProfession`, `PoiTypes`), which is not data.

So `WORKSTATIONS` below is curated. That is a real weakness and it is handled by
checking rather than hoping:

- every profession it names must appear in `language.json`, and every profession
  in `language.json` must appear here -- so a version that adds a profession
  fails the build instead of silently producing a registry with a hole in it;
- every block it names must exist in this package's own `Block` enum for the
  same version, so a typo or a renamed block cannot reach a generated file.

Both checks run at generation time and again in the test suite. `--check`
performs them without writing, which is what CI should call.

# Not generated here: point_of_interest

Job sites are points of interest, but so are beds, bells and nether portals, and
the POI list has no translation keys to read it from. It needs the server data
report, so it is deliberately absent rather than hand-written -- see
PROMPT__VILLAGER_REGISTRIES.md.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PACKAGE_DIRECTORY = Path(__file__).parent.parent
DEFAULT_VERSION = "1.21.11"

# Profession -> the block that creates it. Curated; see the module docstring for
# why, and for the two checks that keep it honest. Professions with no job site
# map to None: they are real professions, not gaps.
WORKSTATIONS: dict[str, str | None] = {
    "armorer": "minecraft:blast_furnace",
    "butcher": "minecraft:smoker",
    "cartographer": "minecraft:cartography_table",
    "cleric": "minecraft:brewing_stand",
    "farmer": "minecraft:composter",
    "fisherman": "minecraft:barrel",
    "fletcher": "minecraft:fletching_table",
    "leatherworker": "minecraft:cauldron",
    "librarian": "minecraft:lectern",
    "mason": "minecraft:stonecutter",
    "shepherd": "minecraft:loom",
    "toolsmith": "minecraft:smithing_table",
    "weaponsmith": "minecraft:grindstone",
    "nitwit": None,
    "none": None,
}


def read_professions(version: str) -> dict[str, str]:
    """Every profession in ``language.json``, mapped to its display name."""
    language_file = PACKAGE_DIRECTORY / "data" / version / "language.json"
    if not language_file.exists():
        raise SystemExit(f"no language.json for {version} at {language_file}")
    language = json.loads(language_file.read_text(encoding="utf-8"))
    prefix = "entity.minecraft.villager."
    return {
        key[len(prefix) :]: value
        for key, value in sorted(language.items())
        if key.startswith(prefix)
    }


def read_block_ids() -> set[str]:
    """The namespaced ids of this package's own ``Block`` enum."""
    # This script runs standalone, so it puts the workspace sources on the path
    # itself rather than relying on editable-install .pth files: on iCloud Drive
    # macOS sets UF_HIDDEN on those and site.py then skips them.
    workspace = PACKAGE_DIRECTORY.parents[2]
    for source in (
        PACKAGE_DIRECTORY.parent,
        workspace / "grimmclub-standardlib" / "srcs",
    ):
        if str(source) not in sys.path:
            sys.path.insert(0, str(source))

    from grimmcraft_data.block import Block

    return {block.string_id for block in Block}


def verify(professions: dict[str, str], block_ids: set[str]) -> list[str]:
    """Return every disagreement between the curated table and the real data."""
    problems: list[str] = []

    missing = sorted(set(professions) - set(WORKSTATIONS))
    for name in missing:
        problems.append(f"{name!r} is in language.json but not in WORKSTATIONS")

    unknown = sorted(set(WORKSTATIONS) - set(professions))
    for name in unknown:
        problems.append(f"{name!r} is in WORKSTATIONS but not in language.json")

    for profession, block in sorted(WORKSTATIONS.items()):
        if block is not None and block not in block_ids:
            problems.append(f"{profession!r} names block {block!r}, which Block does not have")

    return problems


def identifier(name: str) -> str:
    """``bamboo_raft`` -> ``BAMBOO_RAFT``, matching the other generated enums."""
    return name.upper()


def render_professions(version: str, professions: dict[str, str]) -> str:
    lines = [
        '"""Auto-generated. Do not edit by hand; regenerate with',
        '_generate/advanced_villager.py.',
        f"Minecraft Java Edition {version} — {len(professions)} villager professions.",
        "",
        "Each member's .value and .string_id are the namespaced id; .display_name is",
        "the human label; .workstation is the namespaced id of the block that gives a",
        "villager this profession, or None for professions with no job site.",
        "",
        "The profession list comes from Mojang's language.json. The workstation",
        "mapping is curated (Mojang publishes it only in Java source) and verified",
        'against language.json and the Block enum at generation time."""',
        "",
        "from __future__ import annotations",
        "",
        "from grimmclub_standardlib import TYPE_CHECKING, Enum",
        "",
        "if TYPE_CHECKING:",
        "    from .block import Block",
        "",
        "",
        "class VillagerProfession(Enum):",
        "    string_id: str",
        "    display_name: str",
        "    workstation: str | None",
        "",
        "    def __new__(cls, string_id: str, display_name: str, workstation: str | None) -> VillagerProfession:",
        "        obj = object.__new__(cls)",
        "        obj._value_ = string_id",
        "        obj.string_id = string_id",
        "        obj.display_name = display_name",
        "        obj.workstation = workstation",
        "        return obj",
        "",
    ]
    for name, display in professions.items():
        block = WORKSTATIONS[name]
        rendered = "None" if block is None else f'"{block}"'
        lines.append(
            f'    {identifier(name)} = ("minecraft:{name}", "{display}", {rendered})'
        )
    lines += [
        "",
        "",
        "def profession_for_workstation(block: Block | str) -> VillagerProfession | None:",
        '    """The profession a villager takes from ``block``, or None."""',
        '    wanted = getattr(block, "string_id", block)',
        "    for profession in VillagerProfession:",
        "        if profession.workstation == wanted:",
        "            return profession",
        "    return None",
        "",
        "",
        "def workstation_for_profession(profession: VillagerProfession | str) -> str | None:",
        '    """The namespaced block id that creates ``profession``, or None."""',
        '    wanted = getattr(profession, "string_id", profession)',
        "    for candidate in VillagerProfession:",
        "        if candidate.string_id == wanted:",
        "            return candidate.workstation",
        "    return None",
        "",
    ]
    return "\n".join(lines)


def render_workstations(version: str, professions: dict[str, str]) -> str:
    employed = {
        name: block for name, block in WORKSTATIONS.items() if block is not None
    }
    lines = [
        '"""Auto-generated. Do not edit by hand; regenerate with',
        '_generate/advanced_villager.py.',
        f"Minecraft Java Edition {version} — {len(employed)} villager job sites.",
        "",
        "The blocks that give a villager a profession. This is a different idea from",
        "the workstations modelled in grimmcraft-core, which are the blocks a *player*",
        "uses: only brewing_stand is both.",
        "",
        "Each member's .value and .string_id are the namespaced block id;",
        '.profession is the namespaced id of the profession it creates."""',
        "",
        "from __future__ import annotations",
        "",
        "from grimmclub_standardlib import TYPE_CHECKING, Enum",
        "",
        "if TYPE_CHECKING:",
        "    from .block import Block",
        "",
        "",
        "class VillagerWorkstation(Enum):",
        "    string_id: str",
        "    profession: str",
        "",
        "    def __new__(cls, string_id: str, profession: str) -> VillagerWorkstation:",
        "        obj = object.__new__(cls)",
        "        obj._value_ = string_id",
        "        obj.string_id = string_id",
        "        obj.profession = profession",
        "        return obj",
        "",
    ]
    for profession, block in sorted(employed.items(), key=lambda pair: pair[1]):
        short = block.split(":", 1)[1]
        lines.append(f'    {identifier(short)} = ("{block}", "minecraft:{profession}")')
    lines += [
        "",
        "",
        "def workstation_for_block(block: Block | str) -> VillagerWorkstation | None:",
        '    """The job site ``block`` is, or None if it is not one."""',
        '    wanted = getattr(block, "string_id", block)',
        "    for workstation in VillagerWorkstation:",
        "        if workstation.string_id == wanted:",
        "            return workstation",
        "    return None",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", default=DEFAULT_VERSION)
    parser.add_argument(
        "--check", action="store_true", help="verify the curated table, write nothing"
    )
    arguments = parser.parse_args()

    professions = read_professions(arguments.version)
    problems = verify(professions, read_block_ids())
    if problems:
        print(f"{len(problems)} problem(s) with the curated workstation table:")
        for problem in problems:
            print(f"  - {problem}")
        return 1

    print(f"verified {len(professions)} professions against {arguments.version}")
    if arguments.check:
        return 0

    for filename, text in (
        ("villager_profession.py", render_professions(arguments.version, professions)),
        ("villager_workstation.py", render_workstations(arguments.version, professions)),
    ):
        (PACKAGE_DIRECTORY / filename).write_text(text, encoding="utf-8")
        print(f"  wrote {filename}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
