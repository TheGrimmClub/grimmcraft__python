"""Tests for grimmclub_filesystem.config."""

from __future__ import annotations

from pathlib import Path

from grimmclub_filesystem import config


def test_load_defaults_when_missing(tmp_path: Path):
    cfg = config.load_config(tmp_path / "does-not-exist.yaml")
    assert cfg["guard"]["world_dir"] == "./_input"


def test_save_and_load_roundtrip(tmp_path: Path):
    path = tmp_path / "config.yaml"
    data = {"guard": {"world_dir": "./here", "write_docs": False}, "town": {"port": 9000}}
    config.save_config(data, path)
    assert path.is_file()
    loaded = config.load_config(path)
    assert loaded == data


def test_find_config_walks_up(tmp_path: Path):
    (tmp_path / "config.yaml").write_text("guard: {}\n", encoding="utf-8")
    deep = tmp_path / "a" / "b"
    deep.mkdir(parents=True)
    assert config.find_config(deep) == tmp_path / "config.yaml"


def test_save_backs_up_previous_version(tmp_path: Path):
    path = tmp_path / "config.yaml"
    config.save_config({"town": {"port": 8080}}, path)
    # first save: nothing existed before, so no backup yet
    assert not config.backup_path(path).is_file()

    # second save: the previous version is preserved as .bak
    config.save_config({"town": {"port": 9000}}, path)
    backup = config.backup_path(path)
    assert backup.is_file()
    assert config.load_config(backup) == {"town": {"port": 8080}}
    assert config.load_config(path) == {"town": {"port": 9000}}


def test_restore_config_round_trip(tmp_path: Path):
    path = tmp_path / "config.yaml"
    config.save_config({"town": {"port": 8080}}, path)
    config.save_config({"town": {"port": 9000}}, path)

    restored = config.restore_config(path)
    assert restored == path
    assert config.load_config(path) == {"town": {"port": 8080}}


def test_restore_config_without_backup(tmp_path: Path):
    path = tmp_path / "config.yaml"
    config.save_config({"town": {}}, path)  # no prior version -> no backup
    assert config.restore_config(path) is None
