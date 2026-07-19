"""Tests for grimmclub_filesystem.config."""

from __future__ import annotations

from pathlib import Path

import pytest

from grimmclub_filesystem import config


def test_load_returns_registered_defaults_when_missing(tmp_path: Path):
    """The library ships no defaults; a tool registers its own."""
    config.register_defaults("guard", {"world_dir": "./_input"})
    try:
        cfg = config.load_config(tmp_path / "does-not-exist.yaml")
        assert cfg["guard"]["world_dir"] == "./_input"
    finally:
        config.unregister_defaults("guard")


def test_no_defaults_are_registered_by_the_library(tmp_path: Path):
    """A filesystem library has no opinion about what a config should contain."""
    assert config.default_config() == {}
    assert config.load_config(tmp_path / "absent.yaml") == {}


def test_default_config_returns_a_copy(tmp_path: Path):
    config.register_defaults("town", {"port": 8080})
    try:
        first = config.default_config()
        first["town"]["port"] = 9999
        assert config.default_config()["town"]["port"] == 8080, "must not be mutable"
    finally:
        config.unregister_defaults("town")


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


# --- the Config class --------------------------------------------------------
def test_config_reads_lazily(tmp_path: Path):
    """Nothing touches the disk until the data is actually used."""
    path = tmp_path / "config.yaml"
    cfg = config.Config(path)          # file does not exist yet
    path.write_text("town: {port: 8080}\n", encoding="utf-8")
    assert cfg["town"]["port"] == 8080, "the load happened on first access"


def test_config_path_is_a_property(tmp_path: Path):
    cfg = config.Config(str(tmp_path / "config.yaml"))
    assert isinstance(cfg.path, Path), "a str arrives as a SystemPath"
    assert cfg.backup_path.name == "config.yaml.bak"


def test_changing_the_path_drops_stale_data(tmp_path: Path):
    first = tmp_path / "one.yaml"
    first.write_text("town: {port: 1}\n", encoding="utf-8")
    second = tmp_path / "two.yaml"
    second.write_text("town: {port: 2}\n", encoding="utf-8")

    cfg = config.Config(first)
    assert cfg["town"]["port"] == 1
    cfg.path = second
    assert cfg["town"]["port"] == 2, "must re-read, not serve the old file"


def test_loaded_from_disk_distinguishes_defaults(tmp_path: Path):
    path = tmp_path / "config.yaml"
    assert config.Config(path).loaded_from_disk is False
    path.write_text("town: {}\n", encoding="utf-8")
    assert config.Config(path).loaded_from_disk is True


def test_section_and_get_and_set(tmp_path: Path):
    cfg = config.Config(tmp_path / "config.yaml")
    assert cfg.get("town", "port", 8080) == 8080, "absent section falls back"
    cfg.set("town", "port", 9090)
    assert cfg["town"]["port"] == 9090
    assert cfg.get("town", "port") == 9090
    assert "town" in cfg


def test_save_creates_missing_parent_directories(tmp_path: Path):
    cfg = config.Config(tmp_path / "nested" / "deep" / "config.yaml")
    cfg.set("town", "port", 8080)
    assert cfg.save().is_file()


def test_rejects_a_yaml_file_that_is_not_a_mapping(tmp_path: Path):
    path = tmp_path / "config.yaml"
    path.write_text("- one\n- two\n", encoding="utf-8")
    with pytest.raises(ValueError, match="must contain a YAML mapping"):
        config.Config(path).load()


# --- the with block ----------------------------------------------------------
def test_with_block_saves_on_a_clean_exit(tmp_path: Path):
    path = tmp_path / "config.yaml"
    path.write_text("town: {port: 8080}\n", encoding="utf-8")

    with config.Config(path) as cfg:
        cfg["town"]["port"] = 9090

    assert config.load_config(path)["town"]["port"] == 9090
    assert config.backup_path(path).is_file(), "the previous version is kept"


def test_with_block_does_not_save_when_the_body_raises(tmp_path: Path):
    """A half-finished edit is worse than no edit — leave the file alone."""
    path = tmp_path / "config.yaml"
    path.write_text("town: {port: 8080}\n", encoding="utf-8")

    with pytest.raises(RuntimeError):
        with config.Config(path) as cfg:
            cfg["town"]["port"] = 9090
            raise RuntimeError("something went wrong mid-edit")

    assert config.load_config(path)["town"]["port"] == 8080, "unchanged on disk"


def test_with_block_re_raises(tmp_path: Path):
    path = tmp_path / "config.yaml"
    path.write_text("town: {}\n", encoding="utf-8")
    with pytest.raises(KeyError):
        with config.Config(path) as cfg:
            _ = cfg["missing-section"]
