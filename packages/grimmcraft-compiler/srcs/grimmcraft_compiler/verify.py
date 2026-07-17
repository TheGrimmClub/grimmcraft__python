"""Post-emit verification: re-read the datapack on disk and check it is loadable.

This is deliberately independent of the emitter — it walks the produced tree and
confirms the things Minecraft cares about: ``pack.mcmeta`` has the right
``pack_format`` and parses; the folder scheme matches the target; every JSON file
is valid; and every ``function`` call / tag member resolves to a file that exists
in the pack.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from grimmcraft_compiler.diagnostics import Codes, DiagnosticBag
from grimmcraft_compiler.target import Target

_CALL_RE = re.compile(r"\bfunction\s+([a-z0-9_.-]+:[a-z0-9_./-]+)")


def _iter_json(root: Path) -> list[Path]:
    return sorted(root.rglob("*.json"))


def _function_files(root: Path, fdir: str) -> dict[str, Path]:
    """Map ``ns:path`` -> file for every function in the pack."""
    result: dict[str, Path] = {}
    for path in root.rglob("*.mcfunction"):
        rel = path.relative_to(root / "data")
        namespace = rel.parts[0]
        # parts: <ns>/<fdir>/<...path>.mcfunction
        after = rel.parts[1]
        if after != fdir:
            continue
        sub = Path(*rel.parts[2:]).with_suffix("")
        result[f"{namespace}:{sub.as_posix()}"] = path
    return result


def verify_output(pack_path: Path, target: Target, bag: DiagnosticBag) -> None:
    """Verify the emitted datapack at ``pack_path``, appending any failures."""
    info = target.info
    root = Path(pack_path)

    def fail(message: str, hint: str | None = None, source: str | None = None) -> None:
        bag.emit(Codes.VERIFY_FAILED, message, hint=hint, source=source)

    # 1. pack.mcmeta present, valid, correct pack_format.
    meta_path = root / "pack.mcmeta"
    if not meta_path.is_file():
        fail("pack.mcmeta is missing", source=str(root))
        return
    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"pack.mcmeta is not valid JSON: {exc}", source=str(meta_path))
        return
    got = meta.get("pack", {}).get("pack_format")
    if got != info.pack_format:
        fail(
            f"pack.mcmeta pack_format is {got}, expected {info.pack_format} for "
            f"{target.version}",
            hint="recompile for the intended version",
            source=str(meta_path),
        )

    # 2. Folder scheme matches the target.
    fdir = "function" if info.singular_folders else "functions"
    wrong = "functions" if info.singular_folders else "function"
    data = root / "data"
    if data.is_dir():
        for ns_dir in data.iterdir():
            if (ns_dir / wrong).is_dir():
                fail(
                    f"found '{wrong}/' folder but {target.version} expects '{fdir}/'",
                    hint="the folder scheme changed in 1.21 (plural -> singular)",
                    source=str(ns_dir),
                )

    # 3. All JSON parses.
    for json_path in _iter_json(root):
        try:
            json.loads(json_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            fail(f"invalid JSON: {exc}", source=str(json_path))

    # 4. Every function call resolves to a real function file.
    functions = _function_files(root, fdir)
    for fn_id, path in functions.items():
        for line in path.read_text(encoding="utf-8").splitlines():
            for ref in _CALL_RE.findall(line):
                if ref not in functions:
                    fail(
                        f"function '{fn_id}' calls '{ref}', which is not in the pack",
                        hint="every called function must be emitted",
                        source=str(path),
                    )

    # 5. Every function-tag member resolves.
    tags_dir_names = {"function", "functions"}
    for json_path in _iter_json(root):
        parts = json_path.relative_to(root).parts
        if "tags" not in parts:
            continue
        if not any(name in parts for name in tags_dir_names):
            continue
        content = json.loads(json_path.read_text(encoding="utf-8"))
        for member in content.get("values", []):
            member_id = member["id"] if isinstance(member, dict) else member
            if member_id not in functions:
                fail(
                    f"function tag references '{member_id}', which is not in the pack",
                    source=str(json_path),
                )
