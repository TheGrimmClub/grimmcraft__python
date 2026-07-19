"""The mentor: explanations, Markdown loading, and graceful absence."""

from __future__ import annotations

from pathlib import Path

import pytest
from rich.console import Console

from grimmclub_diagnostics import Code, DiagnosticBag, Severity
from grimmclub_mentor import (
    Explanation,
    ExplanationError,
    ExplanationLibrary,
    Mentor,
    Reference,
    parse_markdown,
)

EXAMPLE_CODE = Code("XX1001", "An example problem", Severity.ERROR)
OTHER_CODE = Code("XX2002", "Another problem", Severity.WARNING)

MARKDOWN = """---
codes: [XX1001, YY3003]
summary: This is what went wrong.
lessons:
  - title: The lesson
    target: lessons/01-thing.md
references:
  - docs/reference.md
---
The longer explanation, in Markdown.
"""


def a_bag() -> DiagnosticBag:
    bag = DiagnosticBag()
    bag.emit(EXAMPLE_CODE, "something specific happened", hint="try this")
    bag.emit(OTHER_CODE, "something else happened")
    return bag


# --- the model ---------------------------------------------------------------
def test_an_explanation_must_name_a_code():
    with pytest.raises(ValueError, match="at least one code"):
        Explanation(codes=(), summary="x")


def test_an_explanation_must_have_a_summary():
    with pytest.raises(ValueError, match="no summary"):
        Explanation(codes=("XX1001",), summary="")


# --- Markdown ----------------------------------------------------------------
def test_markdown_front_matter_is_parsed():
    explanation = parse_markdown(MARKDOWN, "test.md")
    assert explanation.codes == ("XX1001", "YY3003")
    assert explanation.summary == "This is what went wrong."
    assert explanation.detail.startswith("The longer explanation")


def test_a_lesson_may_be_given_as_a_bare_path():
    """A teacher writing the fifth lesson of the day gets the short form."""
    explanation = parse_markdown(MARKDOWN, "test.md")
    assert explanation.references == (Reference("reference", "docs/reference.md"),)


def test_missing_front_matter_is_refused_with_the_file_name():
    with pytest.raises(ExplanationError, match="notes.md: no front matter"):
        parse_markdown("Just some prose.", "notes.md")


def test_unclosed_front_matter_is_refused():
    with pytest.raises(ExplanationError, match="not closed"):
        parse_markdown("---\ncodes: [XX1001]\n", "broken.md")


def test_front_matter_without_codes_is_refused():
    with pytest.raises(ExplanationError, match="'codes' must list"):
        parse_markdown("---\nsummary: hi\n---\nbody", "nocodes.md")


def test_front_matter_without_a_summary_is_refused():
    with pytest.raises(ExplanationError, match="'summary' is required"):
        parse_markdown("---\ncodes: [XX1001]\n---\nbody", "nosummary.md")


# --- the library -------------------------------------------------------------
def test_one_explanation_can_cover_several_codes():
    """The *concept* is one thing even when two tools report it differently."""
    library = ExplanationLibrary()
    library.register(parse_markdown(MARKDOWN, "test.md"))
    assert library.explain("XX1001") is library.explain("YY3003")


def test_a_later_registration_wins():
    """How teaching material improves on a package's baseline without a release."""
    library = ExplanationLibrary()
    library.register(Explanation(codes=("XX1001",), summary="first"))
    library.register(Explanation(codes=("XX1001",), summary="second"))
    assert library.explain("XX1001").summary == "second"


def test_unknown_codes_explain_to_nothing():
    assert ExplanationLibrary().explain("ZZ9999") is None


def test_loading_a_directory_registers_every_explanation(tmp_path: Path):
    (tmp_path / "a.md").write_text(MARKDOWN, encoding="utf-8")
    library = ExplanationLibrary()
    assert len(library.load_directory(tmp_path)) == 1
    assert "XX1001" in library


def test_ordinary_lesson_prose_is_skipped_not_rejected(tmp_path: Path):
    """A lessons folder holds prose as well as explanations."""
    (tmp_path / "lesson.md").write_text("# A lesson\n\nSome prose.\n", encoding="utf-8")
    (tmp_path / "explained.md").write_text(MARKDOWN, encoding="utf-8")
    assert len(ExplanationLibrary().load_directory(tmp_path)) == 1


def test_a_missing_directory_is_not_an_error(tmp_path: Path):
    """The teaching material is a separate repository and may not be checked out."""
    assert ExplanationLibrary().load_directory(tmp_path / "absent") == []


# --- the mentor --------------------------------------------------------------
def test_a_note_carries_the_explanation():
    mentor = Mentor()
    mentor.register(Explanation(codes=("XX1001",), summary="because of reasons"))
    note = mentor.note(next(iter(a_bag())))
    assert note.has_explanation
    assert note.explanation.summary == "because of reasons"


def test_a_note_without_an_explanation_is_still_a_note():
    note = Mentor().note(next(iter(a_bag())))
    assert not note.has_explanation
    assert note.code_id == "XX1001"


def test_coverage_counts_what_can_be_taught():
    mentor = Mentor()
    mentor.register(Explanation(codes=("XX1001",), summary="x"))
    assert mentor.coverage(a_bag()) == (1, 2)


def test_unresolved_lessons_are_flagged(tmp_path: Path):
    """Naming a lesson that is not there is better than silence — but say so."""
    mentor = Mentor(lesson_root=tmp_path)
    mentor.register(
        Explanation(
            codes=("XX1001",),
            summary="x",
            lessons=(Reference("Missing", "nowhere.md"),),
        )
    )
    assert mentor.note(next(iter(a_bag()))).unresolved


def test_resolved_lessons_are_not_flagged(tmp_path: Path):
    (tmp_path / "there.md").write_text("# here", encoding="utf-8")
    mentor = Mentor(lesson_root=tmp_path)
    mentor.register(
        Explanation(
            codes=("XX1001",), summary="x", lessons=(Reference("There", "there.md"),)
        )
    )
    assert not mentor.note(next(iter(a_bag()))).unresolved


def test_report_still_works_with_no_explanations_at_all():
    """A mentor that knows nothing must not be worse than no mentor."""
    text = Mentor().report(a_bag(), Console(width=80, quiet=True))
    assert "XX1001" in text
    assert "something specific happened" in text


def test_report_includes_the_teaching():
    mentor = Mentor()
    mentor.register(Explanation(codes=("XX1001",), summary="because of reasons"))
    console = Console(width=100, record=True)
    mentor.report(a_bag(), console)
    # export_text() clears the buffer, so read it once.
    output = console.export_text()
    assert "because of reasons" in output
    assert "1/2 explained" in output


def test_detail_is_withheld_unless_asked():
    """Someone hitting the same error a fifth time does not want the essay."""
    mentor = Mentor()
    mentor.register(
        Explanation(codes=("XX1001",), summary="short", detail="the long version")
    )
    console = Console(width=100, record=True)
    mentor.report(a_bag(), console)
    assert "the long version" not in console.export_text()

    detailed = Console(width=100, record=True)
    mentor.report(a_bag(), detailed, detail=True)
    assert "the long version" in detailed.export_text()


def test_learn_from_a_missing_root_returns_nothing(tmp_path: Path):
    assert Mentor(lesson_root=tmp_path / "absent").learn_from() == []


def test_mentor_knows_nothing_about_any_domain():
    """The property that lets this package move out on its own.

    If it ever imports grimmcraft, extraction stops being a move.
    """
    import ast

    source_root = Path(__file__).resolve().parents[1] / "srcs"
    for module in source_root.rglob("*.py"):
        for node in ast.walk(ast.parse(module.read_text(encoding="utf-8"))):
            name = ""
            if isinstance(node, ast.ImportFrom) and node.module:
                name = node.module
            elif isinstance(node, ast.Import):
                name = node.names[0].name
            assert not name.startswith("grimmcraft"), f"{module.name} imports {name}"
