"""The :class:`Mentor` — diagnostics with a teaching layer on top.

A diagnostic says *what is wrong*. A mentor adds *why it happens* and *where to
learn about it*, without changing the diagnostic itself::

    error GC1001: block 'minecraft:grass' does not exist in 1.21.11.
        hint: use 'minecraft:short_grass'

        mentor  Minecraft renames blocks between versions.
                → Blocks and ids: python/beginners/06-blocks-and-ids.md

Nothing here knows what any code means; the explanations are registered, either
from code or from the teaching material.
"""

from __future__ import annotations

from pathlib import Path

from rich.console import Console
from rich.text import Text

from grimmclub_diagnostics import Diagnostic, DiagnosticBag, Severity
from grimmclub_mentor.library import ExplanationLibrary
from grimmclub_mentor.model import NOTE_HEADING, Explanation, MentorNote, Reference

#: How far the mentor block is indented under its diagnostic.
NOTE_INDENT = "    "


class Mentor:
    """Explains diagnostics, from whatever explanations it has been given.

    ``lesson_root`` is where references are resolved for the "does this lesson
    actually exist?" check. It is optional, and a missing one is not an error —
    the teaching material is a separate repository and may not be checked out.
    """

    def __init__(self, lesson_root: str | Path | None = None) -> None:
        self.library = ExplanationLibrary()
        self.lesson_root = Path(lesson_root) if lesson_root is not None else None

    # --- filling it ----------------------------------------------------------
    def register(self, explanation: Explanation) -> None:
        """Add an explanation from code."""
        self.library.register(explanation)

    def learn_from(self, directory: str | Path | None = None) -> list[Explanation]:
        """Load explanations from the teaching material.

        Defaults to :attr:`lesson_root`. Returns what was loaded, so a caller
        can report "12 explanations from grimmoire" — or notice it got none.
        """
        target = directory if directory is not None else self.lesson_root
        if target is None:
            return []
        return self.library.load_directory(target)

    # --- using it ------------------------------------------------------------
    def resolve(self, reference: Reference) -> bool:
        """Whether a reference can be found on disk under :attr:`lesson_root`."""
        if self.lesson_root is None:
            return False
        return (self.lesson_root / reference.target).exists()

    def note(self, diagnostic: Diagnostic) -> MentorNote:
        """Pair a diagnostic with what can be said about it."""
        explanation = self.library.explain(diagnostic.code.id)
        unresolved: tuple[Reference, ...] = ()
        if explanation is not None and self.lesson_root is not None:
            unresolved = tuple(
                reference
                for reference in (*explanation.lessons, *explanation.references)
                if not self.resolve(reference)
            )
        return MentorNote(
            code_id=diagnostic.code.id,
            message=diagnostic.message,
            explanation=explanation,
            unresolved=unresolved,
        )

    def notes(self, bag: DiagnosticBag) -> list[MentorNote]:
        """A note per diagnostic, in the bag's order."""
        return [self.note(diagnostic) for diagnostic in bag]

    def coverage(self, bag: DiagnosticBag) -> tuple[int, int]:
        """``(explained, total)`` — how much of a report the mentor can teach.

        Worth printing while the explanations are still being written: it says
        exactly which codes still need one.
        """
        notes = self.notes(bag)
        return sum(1 for note in notes if note.has_explanation), len(notes)

    # --- showing it ----------------------------------------------------------
    def render_note(self, note: MentorNote, *, detail: bool = False) -> Text:
        """The teaching block for one diagnostic, indented under it."""
        text = Text()
        explanation = note.explanation
        if explanation is None:
            return text

        text.append(f"{NOTE_INDENT}{NOTE_HEADING}  ", style="bold cyan")
        text.append(f"{explanation.summary}\n")

        if detail and explanation.detail:
            for line in explanation.detail.splitlines():
                text.append(f"{NOTE_INDENT}        {line}\n", style="dim")

        for reference in (*explanation.lessons, *explanation.references):
            marker = "→" if reference not in note.unresolved else "→ (not found)"
            text.append(f"{NOTE_INDENT}        {marker} ", style="cyan")
            text.append(f"{reference.title}: {reference.target}\n", style="dim cyan")

        if detail and explanation.example:
            for line in explanation.example.splitlines():
                text.append(f"{NOTE_INDENT}        {line}\n", style="green")
        return text

    def report(
        self,
        bag: DiagnosticBag,
        console: Console | None = None,
        *,
        detail: bool = False,
    ) -> str:
        """Print the diagnostics with their teaching, and return the plain text.

        Falls back to the bag's own report when there is nothing to add, so a
        mentor with no explanations loaded is never worse than no mentor.
        """
        console = console or Console()
        for severity in (Severity.ERROR, Severity.WARNING, Severity.INFO):
            for diagnostic in bag.of(severity):
                console.print(diagnostic.render())
                note = self.note(diagnostic)
                if note.has_explanation:
                    console.print(self.render_note(note, detail=detail), end="")

        explained, total = self.coverage(bag)
        if total:
            console.print(
                f"\n{explained}/{total} explained "
                f"({len(self.library)} code(s) covered)",
                style="dim",
            )
        return bag.render()
