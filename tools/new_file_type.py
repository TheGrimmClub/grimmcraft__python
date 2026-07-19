#!/usr/bin/env python3
"""Add a new :class:`FileType` to ``grimmclub_filesystem.checks``.

A file type lives in four places — the enum, its match rule, its ``expect_``
guard, and the dispatch in ``expect()`` — and forgetting one of them fails in a
different way each time: a missing match rule silently accepts anything, a
missing dispatch arm quietly falls through to the generic guard. This inserts
all four, in the right sections, or refuses and changes nothing.

    task new-filetype -- YAML --value 102 --layer text --suffixes .yaml,.yml

Layers map to the file's existing sections and decide the numeric band:

    structural   1-99     what the filesystem itself can answer
    text         100-199  decodable as UTF-8
    binary       200+     everything else

Standard library only, so it runs on a fresh clone.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

#: The module this edits, relative to the repository root.
CHECKS_MODULE = Path("packages/grimmclub-filesystem/srcs/grimmclub_filesystem/checks.py")

#: The package's public surface, which also has to learn the new name.
PACKAGE_INIT = Path("packages/grimmclub-filesystem/srcs/grimmclub_filesystem/__init__.py")

#: Layer name -> (inclusive value band, the section comment to insert under).
LAYERS: dict[str, tuple[range, str]] = {
    "structural": (range(1, 100), "# Functions: Layer one — directories, files and links"),
    "text": (range(100, 200), "# Functions, layer 2: Text files"),
    "binary": (range(200, 1000), "# Functions, layer 2: Binary files"),
}


class ScaffoldError(RuntimeError):
    """The edit cannot be made safely, so nothing was changed."""


def _read(path: Path) -> str:
    if not path.is_file():
        raise ScaffoldError(f"cannot find {path} — run this from the repository root")
    return path.read_text(encoding="utf-8")


def _validate(name: str, value: int, layer: str, text: str) -> None:
    """Refuse anything that would produce a broken or duplicate entry."""
    if not name.isidentifier() or not name.isupper():
        raise ScaffoldError(
            f"{name!r} is not a usable member name; use UPPER_SNAKE_CASE"
        )
    if layer not in LAYERS:
        raise ScaffoldError(
            f"unknown layer {layer!r}; choose one of: {', '.join(LAYERS)}"
        )
    band, _ = LAYERS[layer]
    if value not in band:
        raise ScaffoldError(
            f"value {value} is outside the {layer} band "
            f"({band.start}-{band.stop - 1}); the bands are what "
            "is_text/is_binary read, so a value in the wrong one lies"
        )
    if re.search(rf"^    {name} = ", text, flags=re.MULTILINE):
        raise ScaffoldError(f"FileType.{name} already exists")
    if re.search(rf"^    [A-Z_]+ = {value}$", text, flags=re.MULTILINE):
        existing = re.search(rf"^    ([A-Z_]+) = {value}$", text, flags=re.MULTILINE)
        raise ScaffoldError(
            f"value {value} is already used by FileType.{existing.group(1)}"
            if existing
            else f"value {value} is already used"
        )


def _insert_enum_member(text: str, name: str, value: int) -> str:
    """Add the member, keeping the enum ordered by value."""
    members = list(re.finditer(r"^    ([A-Z_]+) = (\d+)$", text, flags=re.MULTILINE))
    if not members:
        raise ScaffoldError("could not find the FileType members")

    following = next((m for m in members if int(m.group(2)) > value), None)
    line = f"    {name} = {value}\n"
    if following is None:
        last = members[-1]
        return text[: last.end() + 1] + line + text[last.end() + 1 :]
    return text[: following.start()] + line + text[following.start() :]


def _insert_suffixes(text: str, name: str, suffixes: list[str]) -> str:
    """Register the extensions, for kinds only a name can identify."""
    if not suffixes:
        return text
    rendered = ", ".join(f'"{suffix}"' for suffix in suffixes)
    entry = f"    FileType.{name}: frozenset({{{rendered}}}),\n"
    marker = "_FILE_TYPE_SUFFIXES: dict[FileType, frozenset[str]] = {\n"
    if marker not in text:
        raise ScaffoldError("could not find _FILE_TYPE_SUFFIXES")
    return text.replace(marker, marker + entry, 1)


def _insert_guard(text: str, name: str, layer: str, what: str) -> str:
    """Add the ``expect_<name>`` function under its layer's section comment."""
    _, section = LAYERS[layer]
    if section not in text:
        raise ScaffoldError(f"could not find the section comment: {section}")

    function = f'''

def expect_{name.lower()}(path: path_like, *, what: str = "{what}") -> SystemPath:
    """Require a {what}."""
    return expect_file(path, what=what, allow_empty=False, file_type=FileType.{name})
'''
    # Insert after the section header's blank lines, before its first function.
    index = text.index(section) + len(section)
    return text[:index] + function + text[index:]


def _insert_dispatch(text: str, name: str) -> str:
    """Add the ``case`` arm to ``expect()``."""
    marker = "        case _:"
    fallback = f"""        case FileType.{name}:
            return expect_{name.lower()}(path, what=label)
"""
    if marker in text:
        return text.replace(marker, fallback + marker, 1)
    # No fallback arm: append after the final case in the match block.
    cases = list(re.finditer(r"^        case FileType\.[A-Z_]+:\n(?:            .*\n)+",
                             text, flags=re.MULTILINE))
    if not cases:
        raise ScaffoldError("could not find the match block in expect()")
    last = cases[-1]
    return text[: last.end()] + fallback + text[last.end() :]


def _export(text: str, name: str) -> str:
    """Add the new guard to the package's public surface."""
    guard = f"expect_{name.lower()}"
    if guard in text:
        return text
    text = text.replace("    expect,\n", f"    expect,\n    {guard},\n", 1)
    return text.replace('    "expect",\n', f'    "expect",\n    "{guard}",\n', 1)


def scaffold(
    name: str,
    value: int,
    layer: str,
    suffixes: list[str],
    what: str,
    root: Path,
    dry_run: bool = False,
) -> str:
    """Perform every edit, or raise having changed nothing."""
    checks_path = root / CHECKS_MODULE
    init_path = root / PACKAGE_INIT

    checks = _read(checks_path)
    init = _read(init_path)

    _validate(name, value, layer, checks)

    updated = _insert_enum_member(checks, name, value)
    updated = _insert_suffixes(updated, name, suffixes)
    updated = _insert_guard(updated, name, layer, what)
    updated = _insert_dispatch(updated, name)
    updated_init = _export(init, name)

    # Parsing before writing means a broken template is caught here rather than
    # by the next person's test run.
    import ast

    try:
        ast.parse(updated)
        ast.parse(updated_init)
    except SyntaxError as error:
        raise ScaffoldError(
            f"the generated code does not parse (line {error.lineno}: {error.msg}); "
            "nothing was written"
        ) from None

    if not dry_run:
        checks_path.write_text(updated, encoding="utf-8")
        init_path.write_text(updated_init, encoding="utf-8")

    edits = [
        ("enum member", CHECKS_MODULE),
        (f"expect_{name.lower()}()", CHECKS_MODULE),
        ("expect() dispatch", CHECKS_MODULE),
        ("export", PACKAGE_INIT),
    ]
    width = max(len(label) for label, _ in edits)
    lines = [f"FileType.{name} = {value} ({layer})"]
    lines += [f"  {label.ljust(width)} -> {where}" for label, where in edits]
    if dry_run:
        lines += ["", "(dry run — nothing written)"]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="new-filetype",
        description="Add a FileType, its guard, its match rule and its dispatch.",
    )
    parser.add_argument("name", help="member name, UPPER_SNAKE_CASE (e.g. YAML)")
    parser.add_argument("--value", type=int, required=True, help="the enum value")
    parser.add_argument(
        "--layer", default="text", choices=sorted(LAYERS), help="which band it belongs to"
    )
    parser.add_argument(
        "--suffixes", default="", help="comma-separated extensions (e.g. .yaml,.yml)"
    )
    parser.add_argument(
        "--what", default="", help="how it reads in an error message"
    )
    parser.add_argument("--dry-run", action="store_true", help="show, do not write")
    parser.add_argument(
        "--root", type=Path, default=Path(__file__).resolve().parent.parent
    )
    arguments = parser.parse_args(argv)

    suffixes = [s.strip() for s in arguments.suffixes.split(",") if s.strip()]
    what = arguments.what or f"{arguments.name} file"

    try:
        print(
            scaffold(
                arguments.name,
                arguments.value,
                arguments.layer,
                suffixes,
                what,
                arguments.root,
                arguments.dry_run,
            )
        )
    except ScaffoldError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
