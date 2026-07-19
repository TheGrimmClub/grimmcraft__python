"""grimmclub-mentor — turn diagnostics into teaching.

A diagnostic tells someone *what* is wrong. A mentor adds *why it happens* and
*where to learn more*, without changing the diagnostic::

    mentor = Mentor(lesson_root="grimmoire")
    mentor.learn_from()                 # explanations from the teaching material
    mentor.report(result.diagnostics)

Generic on purpose. Nothing here knows what any diagnostic code means — codes
are opaque strings, and explanations are *registered* into the model, either
# Includes standard
from code::
or from Markdown in the teaching material, which is how a teacher contributes
without touching Python. Domain packages extend the mentor; the mentor never
reaches into them. That is what will let this package move out to a repository
of its own as a move rather than a rewrite.

A missing teaching repository is not an error: the mentor explains whatever it
has and stays quiet about the rest.
"""

from __future__ import annotations

from grimmclub_mentor.library import (
    ExplanationError,
    ExplanationLibrary,
    parse_markdown,
)
from grimmclub_mentor.mentor import Mentor
from grimmclub_mentor.model import Explanation, MentorNote, Reference

__all__ = [
    "Mentor",
    "Explanation",
    "ExplanationLibrary",
    "ExplanationError",
    "MentorNote",
    "Reference",
    "parse_markdown",
]
