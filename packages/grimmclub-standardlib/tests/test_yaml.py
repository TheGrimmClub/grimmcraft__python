"""The YAML facade: same shape as the JSON one, with a safe default loader."""

from __future__ import annotations

import io

import pytest

from grimmclub_standardlib import yaml


def test_round_trip_through_a_string() -> None:
    original = {"name": "grimmclub", "packages": ["core", "data"], "count": 3}
    assert yaml.loads(yaml.dumps(original)) == original


def test_round_trip_through_a_file() -> None:
    buffer = io.StringIO()
    yaml.dump({"pack_format": 81}, buffer)
    buffer.seek(0)
    assert yaml.load(buffer) == {"pack_format": 81}


def test_load_is_the_safe_loader() -> None:
    """The whole point: ``load`` must not construct arbitrary Python objects."""
    document = "!!python/object/apply:os.system ['echo unsafe']"
    with pytest.raises(yaml.YAMLError):
        yaml.loads(document)


def test_unsafe_load_exists_for_when_it_is_really_wanted() -> None:
    """Named so the choice is visible; here it only builds a plain tuple."""
    assert yaml.unsafe_load("!!python/tuple [1, 2]") == (1, 2)


def test_dump_keeps_key_order() -> None:
    """PyYAML sorts by default, which scrambles a hand-written config file."""
    text = yaml.dumps({"zebra": 1, "apple": 2})
    assert text.index("zebra") < text.index("apple")


def test_dump_can_still_sort_when_asked() -> None:
    text = yaml.dumps({"zebra": 1, "apple": 2}, sort_keys=True)
    assert text.index("apple") < text.index("zebra")


def test_other_names_forward_to_pyyaml() -> None:
    assert yaml.SafeLoader is not None
    assert issubclass(yaml.YAMLError, Exception)


def test_the_package_still_declares_no_dependencies() -> None:
    """The property that lets everything depend on this package.

    PyYAML is imported lazily, so importing the facade must not require it.
    """
    from pathlib import Path

    import tomllib

    root = Path(__file__).resolve().parents[1]
    manifest = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    assert manifest["project"]["dependencies"] == []
