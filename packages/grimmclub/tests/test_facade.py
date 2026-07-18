"""grimmclub facade: names resolve to the real stdlib, and the helpers work."""

from __future__ import annotations

import dataclasses
import enum
import json as real_json
import pathlib

import pytest

import grimmclub


def test_leaf_names_are_the_real_stdlib_objects() -> None:
    assert grimmclub.Path is pathlib.Path
    assert grimmclub.dataclass is dataclasses.dataclass
    assert grimmclub.field is dataclasses.field
    assert grimmclub.StrEnum is enum.StrEnum


def test_modules_are_the_real_modules() -> None:
    assert grimmclub.json is real_json
    assert grimmclub.json.dumps({"ok": True}) == '{"ok": true}'


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
