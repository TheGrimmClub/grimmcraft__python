"""Tests for grimmcraft_world.world (reading world info + datapacks)."""

from __future__ import annotations

import pytest

from grimmclub_filesystem.core import SystemPath
from grimmcraft_world.world import discover_datapacks, locate_world, read_world_info


def test_locate_world_when_nested(tmp_path: SystemPath, tmp_world: SystemPath):
    # tmp_world lives at tmp_path/world; searching from tmp_path should find it
    assert locate_world(tmp_world.parent) == tmp_world


def test_locate_world_missing(tmp_path: SystemPath):
    assert locate_world(tmp_path / "nope") is None


def test_read_world_info(sample_world: SystemPath):
    info = read_world_info(sample_world)
    assert info.name == "world"
    assert info.version == "1.21.11"
    assert info.data_version is not None
    names = {p.name for p in info.datapacks}
    assert "falron" in names


def test_locate_world_when_root_is_world(tmp_world: SystemPath):
    assert locate_world(tmp_world) == tmp_world


def test_datapack_description_and_enabled(sample_world: SystemPath):
    packs = {p.name: p for p in discover_datapacks(sample_world)}
    assert packs["falron"].description == "Falron the Eye of the Storm"
    # with no explicit enabled-set, packs default to enabled
    assert packs["falron"].enabled is True


def test_read_world_info_without_level_dat(tmp_path: SystemPath):
    (tmp_path / "empty").mkdir()
    with pytest.raises(FileNotFoundError):
        read_world_info(tmp_path / "empty")


def test_discover_datapacks_none(tmp_path: SystemPath):
    (tmp_path / "world").mkdir()
    assert discover_datapacks(tmp_path / "world") == []
