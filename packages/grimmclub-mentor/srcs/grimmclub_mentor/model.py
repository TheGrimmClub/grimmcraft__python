"""What a mentor knows: an explanation, and where to read more.

Deliberately free of any domain. An :class:`Explanation` is keyed by diagnostic
*code id* — an opaque string as far as this package is concerned — so the same
model serves a Minecraft compiler, a redstone analyser, or anything else that
emits coded diagnostics.
"""

from __future__ import annotations

# Includes internal
from grimmclub_standardlib import dataclass, field

#: How a mentor note is introduced in a report.
NOTE_HEADING = "mentor"


@dataclass(frozen=True, slots=True)
class Reference:
    """Somewhere to read more: a lesson, a document, a page.

    ``target`` is whatever the reader needs to find it — a path relative to the
    teaching material, or a URL. Not validated here: a mentor that refused to
    mention a lesson because the file was missing would be less useful than one
    that names it and lets the reader look.
    """

    title: str
    target: str

    def __str__(self) -> str:
        return f"{self.title} → {self.target}"


@dataclass(frozen=True, slots=True)
class Explanation:
    """Why a diagnostic happens, and what to learn from it.

    The split between :attr:`summary` and :attr:`detail` is the useful part: a
    report shows the summary inline, and the detail only when asked. A trainee
    hitting the same error for the fifth time does not want the essay again.
    """

    #: Diagnostic code ids this explains, e.g. ``("GC1001", "GD1003")``. One
    #: explanation may cover several codes, because the *concept* is one thing
    #: even when two tools report it differently.
    codes: tuple[str, ...]
    #: One sentence, shown inline with the diagnostic.
    summary: str
    #: The teaching, shown on request. Markdown.
    detail: str = ""
    #: Lessons in the teaching material.
    lessons: tuple[Reference, ...] = ()
    #: Anything else worth reading — reference docs, specifications.
    references: tuple[Reference, ...] = ()
    #: A worked example, shown verbatim.
    example: str = ""
    #: Where this explanation came from, for `mentor --sources`.
    origin: str = "registered"

    def __post_init__(self) -> None:
        if not self.codes:
            raise ValueError("an explanation must name at least one code")
        if not self.summary:
            raise ValueError(f"explanation for {self.codes[0]} has no summary")


@dataclass(slots=True)
class MentorNote:
    """One diagnostic, paired with what the mentor can say about it."""

    code_id: str
    message: str
    explanation: Explanation | None = None
    #: References that could not be resolved on disk, so a report can be honest
    #: about a lesson it is naming but cannot confirm.
    unresolved: tuple[Reference, ...] = field(default_factory=tuple)

    @property
    def has_explanation(self) -> bool:
        return self.explanation is not None
