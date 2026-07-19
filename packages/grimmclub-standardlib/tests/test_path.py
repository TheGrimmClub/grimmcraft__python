"""The logging ``Path``: both spellings, and why the short one cannot be dropped."""

from __future__ import annotations

import pathlib
from collections.abc import Iterator

import pytest

from grimmclub_standardlib import Path, set_debug


@pytest.fixture
def debugging() -> Iterator[None]:
    """Turn debug logging on for one test, and off again whatever happens."""
    set_debug(True)
    try:
        yield
    finally:
        set_debug(False)


def test_it_is_a_pathlib_path(tmp_path: pathlib.Path) -> None:
    """So it mixes freely with plain paths everywhere."""
    assert isinstance(Path(tmp_path), pathlib.Path)


def test_path_arithmetic_keeps_the_logging_subclass(tmp_path: pathlib.Path) -> None:
    assert isinstance(Path(tmp_path) / "sub" / "deeper", Path)


# --- both spellings ----------------------------------------------------------

BOTH_SPELLINGS = [
    ("open_file", "open"),
    ("make_directory", "mkdir"),
    ("create_directory", "mkdir"),
    ("remove_file", "unlink"),
    ("remove_directory", "rmdir"),
]


@pytest.mark.parametrize(("house_name", "pathlib_name"), BOTH_SPELLINGS)
def test_both_spellings_are_the_same_function(house_name: str, pathlib_name: str) -> None:
    """The house name is the definition; pathlib's name is an alias onto it."""
    assert getattr(Path, house_name) is getattr(Path, pathlib_name)


@pytest.mark.parametrize(("_house_name", "pathlib_name"), BOTH_SPELLINGS)
def test_the_pathlib_name_still_overrides(_house_name: str, pathlib_name: str) -> None:
    """The alias must shadow pathlib's own method, or the logging silently stops.

    Renaming instead of aliasing does not rename anything on a subclass: the
    inherited method keeps working and keeps not logging. This has regressed
    once already, which is why it is asserted rather than commented.
    """
    assert getattr(Path, pathlib_name) is not getattr(pathlib.Path, pathlib_name)


# --- the logging itself ------------------------------------------------------


def test_pathlib_internals_still_reach_the_logging(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str], debugging: None
) -> None:
    """``write_text`` calls ``self.open()`` -- proof the short alias is load-bearing."""
    Path(tmp_path / "note.txt").write_text("hello")
    captured = capsys.readouterr()
    assert "open file" in captured.out + captured.err, (
        "write_text no longer reaches the open_file override"
    )


def test_every_operation_logs_under_either_name(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str], debugging: None
) -> None:
    root = Path(tmp_path)
    (root / "house").create_directory()
    (root / "short").mkdir()
    (root / "gone.txt").write_text("x")
    (root / "gone.txt").remove_file()
    (root / "house").remove_directory()

    logged = "".join(capsys.readouterr())
    assert logged.count("make directory") == 2, "create_directory and mkdir must both log"
    assert "remove file" in logged
    assert "remove directory" in logged


def test_normal_runs_are_silent(tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Logging is a teaching aid, not a default -- debug off means nothing printed."""
    Path(tmp_path / "quiet.txt").write_text("x")
    assert "open file" not in "".join(capsys.readouterr())
