"""Tests for grimmclub_filesystem.paths."""

from __future__ import annotations

from pathlib import Path

from grimmclub_filesystem import paths


def test_is_junk_detects_macos_clutter():
    assert paths.is_junk("world/__MACOSX/foo")
    assert paths.is_junk("world/.DS_Store")
    assert not paths.is_junk("world/level.dat")


def test_ensure_dir_creates_nested(tmp_path: Path):
    target = tmp_path / "a" / "b" / "c"
    result = paths.create_full_path(target)
    assert result.is_dir()
    assert result == target
