#!/usr/bin/env python3
"""Emit the game rule registry from the shipped ``language.json``.

Usage:
    python _generate/advanced_game_rule.py
    python _generate/advanced_game_rule.py --version 1.21.11
    python _generate/advanced_game_rule.py --check

# Where the data comes from

Every game rule has a ``gamerule.<name>`` translation key giving the label the
vanilla options screen shows, and about half also have
``gamerule.<name>.description``. The key *is* the rule's identifier — the same
string ``/gamerule`` takes and the same one stored in ``level.dat`` — so the
names here are Mojang's, not a transcription.

That matters. ``grimmcraft-core`` carried a hand-written
``DO_DAYLIGHT_CYCLE = "do_daylight_cycle"``, with a TODO admitting the author
had guessed at snake_case. Of the 63 rules in this file, **none** contain an
underscore. ``/gamerule do_daylight_cycle true`` is not an error in game: it is
silently ignored, which is the worst way to be wrong.

# What is not generated

**Types and defaults.** A rule is boolean or integer and has a vanilla default,
and neither fact is in any file this package ships — they live in Minecraft's
source. Rather than curate 63 values that cannot be verified against anything,
they are simply absent, and ``Game`` treats an unset rule as unset. That matches
how the rest of core behaves: it ships no recipes either, and says so.
"""

from __future__ import annotations

# Includes standard
import argparse
import json
import sys
from pathlib import Path

PACKAGE_DIRECTORY = Path(__file__).parent.parent
DEFAULT_VERSION = "1.21.11"
PREFIX = "gamerule."


def read_rules(version: str) -> dict[str, dict[str, str | None]]:
    """Every game rule in ``language.json``, with its label and description."""
    language_file = PACKAGE_DIRECTORY / "data" / version / "language.json"
    if not language_file.exists():
        raise SystemExit(f"no language.json for {version} at {language_file}")
    language = json.loads(language_file.read_text(encoding="utf-8"))

    rules: dict[str, dict[str, str | None]] = {}
    for key, label in sorted(language.items()):
        if not key.startswith(PREFIX):
            continue
        name = key[len(PREFIX) :]
        # `gamerule.category.chat` and `gamerule.doFireTick.description` are not
        # rules; a rule's key has no further dots.
        if "." in name:
            continue
        rules[name] = {
            "label": label,
            "description": language.get(f"{key}.description"),
        }
    return rules


def identifier(name: str) -> str:
    """``doDaylightCycle`` -> ``DO_DAYLIGHT_CYCLE``, the house enum convention."""
    out: list[str] = []
    for character in name:
        if character.isupper() and out:
            out.append("_")
        out.append(character.upper())
    return "".join(out)


def render(version: str, rules: dict[str, dict[str, str | None]]) -> str:
    lines = [
        '"""Auto-generated. Do not edit by hand; regenerate with',
        "_generate/advanced_game_rule.py.",
        f"Minecraft Java Edition {version} — {len(rules)} game rules.",
        "",
        "Each member's .value and .string_id are the rule name exactly as",
        "/gamerule takes it — camelCase, never snake_case. .label is the vanilla",
        "options-screen text and .description its help line, or None where the",
        'game gives none.',
        "",
        "Types and defaults are deliberately absent: neither is in any data file",
        'this package ships."""',
        "",
        "from __future__ import annotations",
        "",
        "from grimmclub_standardlib import Enum",
        "",
        "",
        "class GameRule(Enum):",
        "    string_id: str",
        "    label: str",
        "    description: str | None",
        "",
        "    def __new__(cls, string_id: str, label: str, description: str | None) -> GameRule:",
        "        obj = object.__new__(cls)",
        "        obj._value_ = string_id",
        "        obj.string_id = string_id",
        "        obj.label = label",
        "        obj.description = description",
        "        return obj",
        "",
    ]
    for name, entry in rules.items():
        label = str(entry["label"]).replace('"', '\\"')
        description = entry["description"]
        rendered = "None" if description is None else '"' + str(description).replace('"', '\\"') + '"'
        lines.append(f'    {identifier(name)} = ("{name}", "{label}", {rendered})')
    lines += [
        "",
        "",
        "def game_rule(name: str) -> GameRule | None:",
        '    """The rule called ``name``, or None if the game has no such rule."""',
        "    for rule in GameRule:",
        "        if rule.string_id == name:",
        "            return rule",
        "    return None",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", default=DEFAULT_VERSION)
    parser.add_argument("--check", action="store_true", help="verify, write nothing")
    arguments = parser.parse_args()

    rules = read_rules(arguments.version)
    snake_case = [name for name in rules if "_" in name]
    if snake_case:
        print(f"unexpected snake_case rule names: {snake_case}", file=sys.stderr)
        return 1

    described = sum(1 for entry in rules.values() if entry["description"])
    print(f"{len(rules)} game rules for {arguments.version}, {described} with descriptions")
    if arguments.check:
        return 0

    target = PACKAGE_DIRECTORY / "game_rule.py"
    target.write_text(render(arguments.version, rules), encoding="utf-8")
    print(f"  wrote {target.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
