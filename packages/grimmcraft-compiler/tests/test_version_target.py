"""Version table + Target resolution: pack_format, folder scheme, components."""

from __future__ import annotations

import pytest

from grimmcraft_compiler.target import Flavor, Target
from grimmcraft_compiler.version import parse_version, resolve_version


def test_parse_version_pads_patch() -> None:
    assert parse_version("1.21") == (1, 21, 0)
    assert parse_version("1.20.4") == (1, 20, 4)


@pytest.mark.parametrize("bad", ["", "1", "x.y", "1.2.3.4"])
def test_parse_version_rejects_bad(bad: str) -> None:
    with pytest.raises(ValueError):
        parse_version(bad)


@pytest.mark.parametrize(
    "version,pack_format,singular,components",
    [
        ("1.20.4", 26, False, False),   # plural folders, NBT
        ("1.20.5", 41, False, True),    # plural folders, components
        ("1.21", 48, True, True),       # singular folders, components
        ("1.21.1", 48, True, True),
    ],
)
def test_version_info(
    version: str, pack_format: int, singular: bool, components: bool
) -> None:
    info = resolve_version(version)
    assert info.pack_format == pack_format
    assert info.singular_folders is singular
    assert info.uses_components is components
    lo, hi = info.supported_formats
    assert lo <= pack_format <= hi


def test_unsupported_version_fails_fast() -> None:
    with pytest.raises(ValueError, match="unsupported Minecraft version"):
        resolve_version("1.99")


def test_target_resolve_and_flavor_parse() -> None:
    target = Target.resolve("1.21.1", "paper")
    assert target.flavor is Flavor.PAPER
    assert target.info.pack_format == 48
    assert str(target) == "1.21.1 paper"


def test_target_rejects_unknown_flavor() -> None:
    with pytest.raises(ValueError, match="unknown flavor"):
        Target.resolve("1.21.1", "spigot")
