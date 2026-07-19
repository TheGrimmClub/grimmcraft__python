"""Generate a datapack of the migrated commands, so the game validates them.

No amount of Python can tell you whether ``minecraft:potion_contents`` takes the
shape we produced — only the game's own parser knows. So ``verify`` writes every
migrated command into ``.mcfunction`` files: load the pack in a 1.21 instance and
each syntax error is reported, with the file and line, by the authority.

Functions are capped at 200 lines so an error message points at a small file, and
named after the coordinates the commands came from so a failure leads straight
back to the command block that needs fixing.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from grimmcraft_migrate.inventory import CommandEntry

#: Maximum commands per generated function file.
MAX_COMMANDS_PER_FUNCTION = 200

#: The pack format for the version being verified against (1.21.4).
VERIFY_PACK_FORMAT = 61

#: Characters allowed in a datapack function path.
_UNSAFE = re.compile(r"[^a-z0-9_./-]+")


def _safe_name(name: str) -> str:
    """A function-path-safe version of ``name``."""
    return _UNSAFE.sub("_", name.lower()) or "commands"


def _group_name(entry: CommandEntry) -> str:
    """Which function file an entry belongs in — its dimension, or 'unknown'."""
    if entry.dimension is None:
        return "unknown"
    return _safe_name(entry.dimension.split(":")[-1])


def build_verification_pack(
    entries: list[CommandEntry],
    output_directory: str | Path,
    *,
    namespace: str = "migration_check",
) -> Path:
    """Write a datapack of ``entries`` and return its root directory.

    Commands are grouped by source dimension, then chunked; every function file
    carries a header naming the coordinate range it covers.
    """
    root = Path(output_directory)
    functions = root / "data" / namespace / "function"
    functions.mkdir(parents=True, exist_ok=True)

    (root / "pack.mcmeta").write_text(
        json.dumps(
            {
                "pack": {
                    "pack_format": VERIFY_PACK_FORMAT,
                    "description": (
                        "Migrated commands, for syntax checking only. "
                        "Loading this pack reports any command the game rejects."
                    ),
                }
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    grouped: dict[str, list[CommandEntry]] = {}
    for entry in entries:
        grouped.setdefault(_group_name(entry), []).append(entry)

    written: list[str] = []
    for group, group_entries in sorted(grouped.items()):
        for index in range(0, len(group_entries), MAX_COMMANDS_PER_FUNCTION):
            chunk = group_entries[index : index + MAX_COMMANDS_PER_FUNCTION]
            number = index // MAX_COMMANDS_PER_FUNCTION
            name = f"{group}_{number:03d}"
            lines = [
                f"# Migrated commands from {group}, part {number}",
                f"# {len(chunk)} command(s); each line's source follows it as a comment",
            ]
            for entry in chunk:
                lines.append(f"# from {entry.location}")
                # A leading slash is valid at a command block but not in a
                # function file, so it is stripped here.
                lines.append(entry.command.lstrip("/"))
            (functions / f"{name}.mcfunction").write_text(
                "\n".join(lines) + "\n", encoding="utf-8"
            )
            written.append(f"{namespace}:{name}")

    # An index function that calls every chunk, so one /function checks the lot.
    index_lines = ["# Runs every migrated command — expect errors only if a command is wrong"]
    index_lines += [f"function {reference}" for reference in written]
    (functions / "run_all.mcfunction").write_text(
        "\n".join(index_lines) + "\n", encoding="utf-8"
    )

    (root / "README.md").write_text(
        _instructions(namespace, written), encoding="utf-8"
    )
    return root


def _instructions(namespace: str, written: list[str]) -> str:
    listing = "\n".join(f"- `{reference}`" for reference in written) or "- (none)"
    return f"""# Migration verification pack

Every migrated command, written into function files so **Minecraft's own parser**
checks them. Python cannot confirm that a data component takes the shape we
produced; the game can.

## How to use it

1. Copy this folder into `saves/<world>/datapacks/`.
2. Run `/reload` in a **1.21** instance.
3. Any command the game rejects is reported in the log with its file and line —
   that line is the migrated command, and the comment directly above it names the
   coordinates it came from.

Loading alone surfaces syntax errors. To also execute them (which will have real
effects in the world — use a scratch world):

```
/function {namespace}:run_all
```

## Functions

{listing}
"""
