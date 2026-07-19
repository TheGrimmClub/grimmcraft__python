"""The round-trip contract: decompile, recompile, and diff against the original.

For any pack the **compiler** produced, re-emitting the decompiled IR must
reproduce the tree byte for byte.  That is a strong statement about the
reader/:class:`~grimmcraft_compiler.dialect.Dialect` symmetry, and it doubles as
a regression guard on the *forward* compiler: if lowering changes shape, these
diffs light up.

Two levels are checkable:

* :data:`Level.IR` — re-emit the lifted IR.  Expected to be byte-identical for
  compiler-generated packs, and identical *modulo formatting* for hand-written
  ones (whose JSON indentation and blank lines are their own).
* :data:`Level.MACHINE` — re-lower the reconstructed machines through the real
  compiler pipeline.  This is the strict "``compile(decompile(pack)) == pack``"
  claim, and it only applies to grimmcraft-generated packs.
"""

from __future__ import annotations

import difflib
import json
import tempfile
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from grimmcraft_compiler.emit import emit
from grimmcraft_compiler.ir import Datapack
from grimmcraft_compiler.lower import lower
from grimmcraft_compiler.target import Target
from grimmcraft_control.machine import Machine
from grimmcraft_decompiler.source import PackSource


class Level(Enum):
    """Which reconstruction to re-emit when checking the round-trip."""

    #: Re-emit the lifted IR (works for any pack).
    IR = "ir"
    #: Re-lower the reconstructed machines (grimmcraft packs only).
    MACHINE = "machine"


@dataclass(frozen=True, slots=True)
class FileDiff:
    """One file that differs between the original pack and the re-emitted one."""

    path: str
    #: ``"missing"`` (not re-emitted), ``"extra"`` (only re-emitted), ``"changed"``.
    kind: str
    diff: str = ""

    def render(self) -> str:
        header = f"{self.kind}: {self.path}"
        return f"{header}\n{self.diff}" if self.diff else header


@dataclass(slots=True)
class DiffReport:
    """The outcome of a round-trip: every file that failed to reproduce."""

    level: Level
    target: Target
    files_compared: int = 0
    differences: list[FileDiff] = field(default_factory=list)

    @property
    def identical(self) -> bool:
        """True when the re-emitted pack matched the original exactly."""
        return not self.differences

    def summary(self) -> str:
        """A one-line verdict, suitable for a CLI or a test failure message."""
        if self.identical:
            return (
                f"round-trip ({self.level.value}) identical: "
                f"{self.files_compared} file(s) reproduced for {self.target}"
            )
        kinds = ", ".join(
            f"{sum(1 for d in self.differences if d.kind == kind)} {kind}"
            for kind in ("changed", "missing", "extra")
            if any(d.kind == kind for d in self.differences)
        )
        return (
            f"round-trip ({self.level.value}) differs: {kinds} "
            f"of {self.files_compared} file(s) for {self.target}"
        )

    def render(self, *, limit: int = 5) -> str:
        """The summary plus the first ``limit`` diffs, for a readable report."""
        lines = [self.summary()]
        for difference in self.differences[:limit]:
            lines.append(difference.render())
        remaining = len(self.differences) - limit
        if remaining > 0:
            lines.append(f"… and {remaining} more")
        return "\n".join(lines)


def _read_tree(root: Path) -> dict[str, str]:
    """Every text file under ``root``, keyed by relative POSIX path."""
    files: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        try:
            files[path.relative_to(root).as_posix()] = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
    return files


def _models(path: str) -> bool:
    """Whether the IR represents ``path`` at all.

    A datapack may carry files that are not datapack *content* — a README, the
    generator scripts that produced it, ``INSTALL.md``.  The IR has no model for
    those, so a structural comparison must not count them as losses.
    """
    return path == "pack.mcmeta" or (
        path.startswith("data/") and path.endswith((".mcfunction", ".json"))
    )


def _equivalent(path: str, before: str, after: str) -> bool:
    """Whether two versions of ``path`` are the same *content*, ignoring layout.

    Hand-written packs choose their own JSON indentation and often omit the
    trailing newline; the emitter always normalises both.  Comparing parsed JSON
    and newline-stripped text is what "identical modulo whitespace" means.
    """
    if before == after:
        return True
    if path.endswith(".json"):
        try:
            return bool(json.loads(before) == json.loads(after))
        except json.JSONDecodeError:
            return False
    return before.rstrip("\n") == after.rstrip("\n")


def _compare(
    original: dict[str, str],
    produced: dict[str, str],
    *,
    strict: bool = True,
) -> list[FileDiff]:
    """Diff two file maps.

    ``strict`` demands byte-for-byte equality across every file — the contract
    for compiler-generated packs.  Otherwise only files the IR models are
    compared, and only up to formatting.
    """
    paths = set(original) | set(produced)
    if not strict:
        paths = {path for path in paths if _models(path)}
    differences: list[FileDiff] = []
    for path in sorted(paths):
        before, after = original.get(path), produced.get(path)
        if before is not None and after is not None:
            if before == after or (not strict and _equivalent(path, before, after)):
                continue
        if before is None:
            differences.append(FileDiff(path, "extra"))
        elif after is None:
            differences.append(FileDiff(path, "missing"))
        else:
            diff = "".join(
                difflib.unified_diff(
                    before.splitlines(keepends=True),
                    after.splitlines(keepends=True),
                    fromfile=f"a/{path}",
                    tofile=f"b/{path}",
                    n=1,
                )
            )
            differences.append(FileDiff(path, "changed", diff))
    return differences


def roundtrip(
    source: PackSource,
    pack: Datapack,
    target: Target,
    *,
    machines: list[Machine[Any]] | None = None,
    level: Level = Level.IR,
    strict: bool = True,
) -> DiffReport:
    """Re-emit ``pack`` (or ``machines``) and diff the result against ``source``.

    At :data:`Level.MACHINE` the reconstructed machines go back through the real
    :func:`~grimmcraft_compiler.lower.lower` before emission, so the check
    exercises the genuine forward pipeline rather than echoing the IR back.  The
    original description is reused verbatim — it is part of ``pack.mcmeta`` and
    therefore part of the byte comparison.

    ``strict`` (the default) is the byte-for-byte contract that holds for
    compiler-generated packs.  Pass ``strict=False`` for hand-written packs,
    where the guarantee is only that the modelled content survives — formatting
    the emitter normalises (JSON indentation, trailing newlines) and files the IR
    does not model (READMEs, generator scripts) are then ignored.
    """
    if level is Level.MACHINE:
        if machines is None:
            raise ValueError("machine-level round-trip needs the lifted machines")
        rebuilt = lower(machines, pack.namespace, description=pack.description)
    else:
        rebuilt = pack

    with tempfile.TemporaryDirectory(prefix="grimmcraft-roundtrip-") as tmp:
        out = Path(tmp) / "pack"
        emit(rebuilt, target, out)
        produced = _read_tree(out)

    original = dict(source.files)
    differences = _compare(original, produced, strict=strict)
    compared = set(original) | set(produced)
    if not strict:
        compared = {path for path in compared if _models(path)}
    return DiffReport(
        level=level,
        target=target,
        files_compared=len(compared),
        differences=differences,
    )
