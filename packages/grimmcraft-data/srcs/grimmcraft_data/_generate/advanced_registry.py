#!/usr/bin/env python3
"""Emit exhaustive registry Enums from Mojang's `reports/registries.json`.

minecraft-data omits many vanilla registries.  The authoritative, complete source
is Mojang's data-generator report, produced by:

    java -DbundlerMainClass=net.minecraft.data.Main -jar server.jar --reports
    # -> generated/reports/registries.json

Its shape is::

    { "minecraft:sound_event": {
        "protocol_id": 12,
        "default": "minecraft:...",              # optional
        "entries": { "minecraft:entity.zombie.ambient": {"protocol_id": 0}, ... }
      }, ... }

For each requested registry this writes `../{registry_name}.py` containing an
`Enum` whose `.value` is the entry `protocol_id` and `.string_id` the namespaced
id, sorted by `protocol_id` for a stable file.

Usage:
    # from a local report (recommended):
    python _generate/advanced_registry.py --input registries.json
    python _generate/advanced_registry.py --input registries.json sound_event menu
    python _generate/advanced_registry.py --input registries.json --list

There is no verified public mirror of this file, so `--version` is only honoured
if `MIRROR_URL` below is set to one you trust; otherwise pass `--input`.
"""

import keyword
import urllib.request

from grimmclub_standardlib import SystemPath, json, re, sys

# No trustworthy public mirror is hardcoded; set this to a URL template you trust
# (must contain "{version}") to enable `--version` downloads.
MIRROR_URL = None

PKG_DIR = SystemPath(__file__).parent.parent

# Registries that PrismarineJS/minecraft-data does not ship; a sensible default.
DEFAULT_REGISTRIES = [
    "sound_event",
    "block_entity_type",
    "game_event",
    "menu",
    "mob_effect",
    "villager_profession",
    "painting_variant",
    "banner_pattern",
    "dimension_type",
]


def fetch_text(url):
    with urllib.request.urlopen(url, timeout=30) as r:
        return r.read().decode("utf-8")


def member_name(full_id):
    """Turn a namespaced id into a valid, unique-ish enum member name.

    Superset of the enum scripts' `member_name`: entry ids in these registries
    contain dots/slashes (e.g. 'minecraft:entity.zombie.ambient'), so any
    character outside [A-Z0-9_] is collapsed to '_'.
    """
    name = full_id.split(":", 1)[-1].upper()
    name = re.sub(r"[^0-9A-Z_]", "_", name)
    if not name[:1].isalpha() and name[:1] != "_":
        name = "N_" + name          # names can't start with a digit
    if keyword.iskeyword(name.lower()):
        name += "_"
    return name


def class_name(registry):
    """'minecraft:block_entity_type' -> 'BlockEntityType'."""
    base = registry.split(":", 1)[-1]
    return "".join(part.capitalize() for part in base.split("_"))


def short_name(registry):
    """'minecraft:sound_event' -> 'sound_event'."""
    return registry.split(":", 1)[-1]


def load_report(args):
    """Return the parsed registries object, or exit with instructions."""
    if "--input" in args:
        path = SystemPath(args[args.index("--input") + 1])
        return json.loads(path.read_text(encoding="utf-8"))
    if "--version" in args:
        version = args[args.index("--version") + 1]
        if MIRROR_URL:
            return json.loads(fetch_text(MIRROR_URL.format(version=version)))
        sys.exit(
            f"No trusted mirror configured for --version {version}.\n"
            "Generate the report locally and pass it explicitly:\n"
            "  java -DbundlerMainClass=net.minecraft.data.Main -jar server.jar --reports\n"
            "  python _generate/advanced_registry.py --input generated/reports/registries.json"
        )
    sys.exit(
        "No registries file provided. Produce one with:\n"
        "  java -DbundlerMainClass=net.minecraft.data.Main -jar server.jar --reports\n"
        "then pass it with:\n"
        "  python _generate/advanced_registry.py --input generated/reports/registries.json"
    )


def resolve_registry(report, requested):
    """Accept 'menu' or 'minecraft:menu'; return (full_key, data) or (None, None)."""
    for candidate in (requested, f"minecraft:{requested}"):
        if candidate in report:
            return candidate, report[candidate]
    return None, None


def build_module(full_key, data, version):
    entries = data.get("entries", {})
    # sort by protocol_id for a stable, ascending file
    ordered = sorted(entries.items(), key=lambda kv: kv[1].get("protocol_id", 0))
    cls = class_name(full_key)

    version_note = version or "unknown"
    lines = [
        '"""Auto-generated from Mojang data-generator `reports/registries.json`.',
        "",
        f"Registry: {full_key}",
        f"Minecraft Java Edition {version_note} — {len(ordered)} entries.",
        "",
        "Each member's .value is the entry's `protocol_id` (int) and .string_id is",
        "the namespaced id.  NOTE: protocol_ids are stable within a version but not",
        "across versions.",
        'Do not edit by hand; regenerate with _generate/advanced_registry.py."""',
        "",
        "from __future__ import annotations",
        "",
        "from grimmclub_standardlib import Enum",
        "",
        "",
        f"class {cls}(Enum):",
        "    string_id: str",
        "",
        "    def __new__(cls, protocol_id, string_id):",
        "        obj = object.__new__(cls)",
        "        obj._value_ = protocol_id",
        "        obj.string_id = string_id",
        "        return obj",
        "",
    ]
    seen = set()
    for entry_id, meta in ordered:
        name = member_name(entry_id)
        while name in seen:
            name += "_"
        seen.add(name)
        pid = meta.get("protocol_id", 0)
        lines.append(f'    {name} = ({pid}, {json.dumps(entry_id)})')
    lines.append("")
    return cls, "\n".join(lines)


def main():
    args = list(sys.argv[1:])
    report = load_report(args)

    if "--list" in args:
        print("\n".join(sorted(report.keys())))
        return

    version = args[args.index("--version") + 1] if "--version" in args else None

    # positional args (skip flags and their values)
    flags_with_value = {"--input", "--version"}
    positional = []
    i = 0
    while i < len(args):
        a = args[i]
        if a in flags_with_value:
            i += 2
            continue
        if a.startswith("-"):
            i += 1
            continue
        positional.append(a)
        i += 1
    requested = positional or DEFAULT_REGISTRIES

    for reg in requested:
        full_key, data = resolve_registry(report, reg)
        if data is None:
            print(f"! registry not found in report: {reg} (try --list)")
            continue
        cls, code = build_module(full_key, data, version)
        out = PKG_DIR / f"{short_name(full_key)}.py"
        out.write_text(code)
        print(f"Wrote {out} — {cls} ({len(data.get('entries', {}))} entries)")


if __name__ == "__main__":
    main()
