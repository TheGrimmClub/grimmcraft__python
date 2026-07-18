"""grimmclub facade: names resolve to the real stdlib, and the helpers work."""

from __future__ import annotations

import dataclasses
import enum
import json as real_json
import pathlib

import pytest

import grimmclub


def test_plain_leaf_names_are_the_real_stdlib_objects() -> None:
    assert grimmclub.dataclass is dataclasses.dataclass
    assert grimmclub.field is dataclasses.field
    assert grimmclub.StrEnum is enum.StrEnum


def test_path_is_a_logging_pathlib_subclass() -> None:
    # Same API — it IS a pathlib.Path — but a wrapper we can hang logging on.
    assert issubclass(grimmclub.Path, pathlib.Path)
    p = grimmclub.Path("/tmp/x")
    assert isinstance(p, pathlib.Path)
    assert (p / "sub").__class__ is grimmclub.Path  # wrapping follows the chain


def test_json_wrapper_matches_stdlib_and_forwards_extras() -> None:
    assert grimmclub.json.dumps({"ok": True}) == real_json.dumps({"ok": True})
    assert grimmclub.json.loads('{"a": 1}') == {"a": 1}
    # anything not overridden is forwarded to stdlib json
    assert grimmclub.json.JSONDecodeError is real_json.JSONDecodeError


def test_wrappers_log_only_in_debug(
    capsys: pytest.CaptureFixture[str], tmp_path: pathlib.Path
) -> None:
    target = grimmclub.Path(tmp_path) / "note.txt"

    grimmclub.set_debug(False)
    target.write_text("hi")
    assert target.read_text() == "hi"
    grimmclub.json.dumps({"a": 1})
    assert capsys.readouterr().err == ""  # silent when debug is off

    grimmclub.set_debug(True)
    target.write_text("bye")
    grimmclub.json.dumps({"a": 1})
    err = capsys.readouterr().err
    assert "write_text" in err and "json.dumps" in err
    grimmclub.set_debug(False)


def test_everything_in_all_is_importable() -> None:
    for name in grimmclub.__all__:
        assert hasattr(grimmclub, name), name


def test_log_and_banner_go_to_the_right_stream(capsys: pytest.CaptureFixture[str]) -> None:
    grimmclub.log("hello", 42)
    grimmclub.banner("Title", width=20, char="-")
    captured = capsys.readouterr()
    assert "[grimmclub] hello 42" in captured.err  # log -> stderr
    assert "Title" in captured.out and captured.out.startswith("---")  # banner -> stdout


def test_debug_respects_the_toggle(capsys: pytest.CaptureFixture[str]) -> None:
    grimmclub.set_debug(False)
    grimmclub.debug("quiet")
    assert capsys.readouterr().err == ""

    grimmclub.set_debug(True)
    grimmclub.debug("loud")
    assert "loud" in capsys.readouterr().err
    grimmclub.set_debug(False)


def test_strenum_re_export_behaves() -> None:
    class Color(grimmclub.StrEnum):
        RED = "red"

    assert Color.RED == "red"
