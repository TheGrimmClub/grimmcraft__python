"""The library of explanations, and the two ways things get into it.

**Registration**, from code::

    library.register(Explanation(codes=("GC1001",), summary="…"))

**Discovery**, from Markdown with front matter — which is how the teaching
material contributes, so a teacher edits prose rather than Python::

    ---
    codes: [GC1001, GD1003]
    summary: Minecraft renames blocks between versions.
    lessons:
      - title: Blocks and ids
        target: python/beginners/06-blocks-and-ids.md
    ---
    The longer explanation goes here, in Markdown.

Both end up in the same model. Neither is privileged: a package can register a
baseline explanation in Python and the teaching material can override it with a
richer one, which is what lets lessons improve without a release.
"""

from __future__ import annotations

# Includes standard
from dataclasses import replace
from pathlib import Path

# Includes external
import yaml

# Includes internal
from grimmclub_mentor.model import Explanation, Reference

#: Delimiter for the front-matter block at the top of a Markdown file.
FRONT_MATTER_FENCE = "---"


class ExplanationError(ValueError):
    """A Markdown explanation could not be read, naming the file and why."""


def _references(raw: object, kind: str, origin: str) -> tuple[Reference, ...]:
    """Parse the ``lessons``/``references`` front-matter field.

    Accepts a bare string, a list of strings, or a list of
    ``{title, target}`` mappings — because a teacher writing the fifth lesson of
    the day should be able to write the short form.
    """
    if raw is None:
        return ()
    if isinstance(raw, str):
        raw = [raw]
    if not isinstance(raw, list):
        raise ExplanationError(f"{origin}: '{kind}' must be a string or a list")

    found: list[Reference] = []
    for entry in raw:
        if isinstance(entry, str):
            # Short form: the target doubles as the title, tidied up.
            found.append(Reference(title=Path(entry).stem.replace("-", " "), target=entry))
        elif isinstance(entry, dict) and "target" in entry:
            found.append(
                Reference(
                    title=str(entry.get("title", entry["target"])),
                    target=str(entry["target"]),
                )
            )
        else:
            raise ExplanationError(
                f"{origin}: each '{kind}' entry must be a path or a {{{{title, target}}}} mapping"
            )
    return tuple(found)


def parse_markdown(text: str, origin: str = "<string>") -> Explanation:
    """Read one Markdown explanation with YAML front matter."""
    stripped = text.lstrip()
    if not stripped.startswith(FRONT_MATTER_FENCE):
        raise ExplanationError(
            f"{origin}: no front matter — an explanation must begin with a "
            f"'{FRONT_MATTER_FENCE}' block naming the codes it explains"
        )

    _, _, rest = stripped.partition(FRONT_MATTER_FENCE)
    front, fence, body = rest.partition(f"\n{FRONT_MATTER_FENCE}")
    if not fence:
        raise ExplanationError(f"{origin}: front matter is not closed")

    try:
        header = yaml.safe_load(front) or {}
    except yaml.YAMLError as error:
        raise ExplanationError(f"{origin}: front matter is not valid YAML: {error}") from None
    if not isinstance(header, dict):
        raise ExplanationError(f"{origin}: front matter must be a mapping")

    codes = header.get("codes")
    if isinstance(codes, str):
        codes = [codes]
    if not isinstance(codes, list) or not codes:
        raise ExplanationError(f"{origin}: 'codes' must list at least one code id")

    summary = header.get("summary")
    if not summary:
        raise ExplanationError(f"{origin}: 'summary' is required — one sentence")

    return Explanation(
        codes=tuple(str(code) for code in codes),
        summary=str(summary),
        detail=body.lstrip("\n").rstrip(),
        lessons=_references(header.get("lessons"), "lessons", origin),
        references=_references(header.get("references"), "references", origin),
        example=str(header.get("example", "")),
        origin=origin,
    )


class ExplanationLibrary:
    """Explanations, keyed by the diagnostic codes they explain."""

    def __init__(self) -> None:
        self._by_code: dict[str, Explanation] = {}

    def register(self, explanation: Explanation) -> None:
        """Add an explanation under every code it names.

        A later registration replaces an earlier one for the same code, which is
        deliberate: it is how teaching material improves on a package's built-in
        baseline without that package changing.
        """
        for code in explanation.codes:
            self._by_code[code] = explanation

    def explain(self, code_id: str) -> Explanation | None:
        """The explanation for a code, or ``None`` if nothing covers it yet."""
        return self._by_code.get(code_id)

    def load_file(self, path: str | Path, *, base: Path | None = None) -> Explanation:
        """Read one Markdown explanation and register it."""
        target = Path(path)
        origin = str(target.relative_to(base)) if base else str(target)
        explanation = parse_markdown(target.read_text(encoding="utf-8"), origin)
        self.register(explanation)
        return explanation

    def load_directory(self, directory: str | Path) -> list[Explanation]:
        """Register every ``.md`` explanation under ``directory``.

        Missing directories are **not** an error: the teaching material is a
        separate repository and may simply not be checked out. A mentor with no
        lessons still explains what it was given in code; one that refused to
        start would be worse than useless.

        Files without front matter are skipped rather than rejected — a lessons
        folder contains prose as well as explanations.
        """
        root = Path(directory)
        if not root.is_dir():
            return []

        loaded: list[Explanation] = []
        for candidate in sorted(root.rglob("*.md")):
            text = candidate.read_text(encoding="utf-8")
            if not text.lstrip().startswith(FRONT_MATTER_FENCE):
                continue  # ordinary lesson prose, not an explanation
            try:
                explanation = parse_markdown(text, str(candidate.relative_to(root)))
            except ExplanationError:
                continue  # front matter that is not ours; leave it alone
            self.register(explanation)
            loaded.append(explanation)
        return loaded

    def with_origin(self, explanation: Explanation, origin: str) -> Explanation:
        """A copy of ``explanation`` tagged with where it came from."""
        return replace(explanation, origin=origin)

    @property
    def codes(self) -> list[str]:
        """Every code that has an explanation, sorted."""
        return sorted(self._by_code)

    def __len__(self) -> int:
        return len(self._by_code)

    def __contains__(self, code_id: object) -> bool:
        return code_id in self._by_code
