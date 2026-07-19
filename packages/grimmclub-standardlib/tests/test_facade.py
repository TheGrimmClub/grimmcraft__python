"""grimmclub-standardlib facade: names resolve to the real stdlib, and the helpers work."""

from __future__ import annotations

import dataclasses
import enum
import json as real_json
import pathlib

import pytest

import grimmclub_standardlib


def test_plain_leaf_names_are_the_real_stdlib_objects() -> None:
    assert grimmclub_standardlib.dataclass is dataclasses.dataclass
    assert grimmclub_standardlib.field is dataclasses.field
    assert grimmclub_standardlib.StrEnum is enum.StrEnum


def test_path_is_a_logging_pathlib_subclass() -> None:
    # Same API — it IS a pathlib.Path — but a wrapper we can hang logging on.
    assert issubclass(grimmclub_standardlib.Path, pathlib.Path)
    p = grimmclub_standardlib.Path("/tmp/x")
    assert isinstance(p, pathlib.Path)
    assert (p / "sub").__class__ is grimmclub_standardlib.Path  # wrapping follows the chain


def test_json_wrapper_matches_stdlib_and_forwards_extras() -> None:
    assert grimmclub_standardlib.json.dumps({"ok": True}) == real_json.dumps({"ok": True})
    assert grimmclub_standardlib.json.loads('{"a": 1}') == {"a": 1}
    # anything not overridden is forwarded to stdlib json
    assert grimmclub_standardlib.json.JSONDecodeError is real_json.JSONDecodeError


def test_wrappers_log_only_in_debug(
    capsys: pytest.CaptureFixture[str], tmp_path: pathlib.Path
) -> None:
    target = grimmclub_standardlib.Path(tmp_path) / "note.txt"

    grimmclub_standardlib.set_debug(False)
    target.write_text("hi")
    assert target.read_text() == "hi"
    grimmclub_standardlib.json.dumps({"a": 1})
    assert capsys.readouterr().err == ""  # silent when debug is off

    grimmclub_standardlib.set_debug(True)
    target.write_text("bye")
    grimmclub_standardlib.json.dumps({"a": 1})
    err = capsys.readouterr().err
    assert "write_text" in err and "json.dumps" in err
    grimmclub_standardlib.set_debug(False)


def test_everything_in_all_is_importable() -> None:
    for name in grimmclub_standardlib.__all__:
        assert hasattr(grimmclub_standardlib, name), name


def test_log_and_banner_go_to_the_right_stream(capsys: pytest.CaptureFixture[str]) -> None:
    grimmclub_standardlib.log("hello", 42)
    grimmclub_standardlib.banner("Title", width=20, char="-")
    captured = capsys.readouterr()
    assert "[grimmclub] hello 42" in captured.err  # log -> stderr
    assert "Title" in captured.out and captured.out.startswith("---")  # banner -> stdout


def test_debug_respects_the_toggle(capsys: pytest.CaptureFixture[str]) -> None:
    grimmclub_standardlib.set_debug(False)
    grimmclub_standardlib.debug("quiet")
    assert capsys.readouterr().err == ""

    grimmclub_standardlib.set_debug(True)
    grimmclub_standardlib.debug("loud")
    assert "loud" in capsys.readouterr().err
    grimmclub_standardlib.set_debug(False)


def test_strenum_re_export_behaves() -> None:
    class Color(grimmclub_standardlib.StrEnum):
        RED = "red"

    assert Color.RED == "red"


# --- the layering ------------------------------------------------------------
def test_this_package_has_no_grimmclub_dependencies():
    """It sits at the bottom of the stack, so it must depend on nothing of ours.

    If this ever fails, something above has been imported from below and the
    layering has inverted — which is how import cycles start.
    """
    import ast
    import pathlib

    source_root = pathlib.Path(__file__).resolve().parents[1] / "srcs"
    for module in source_root.rglob("*.py"):
        tree = ast.parse(module.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            imported = ""
            if isinstance(node, ast.ImportFrom) and node.module:
                imported = node.module
            elif isinstance(node, ast.Import):
                imported = node.names[0].name
            top = imported.split(".")[0]
            assert not (top.startswith("grimmclub") and top != "grimmclub_standardlib"), (
                f"{module.name} imports {imported}"
            )
