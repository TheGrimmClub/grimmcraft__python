"""Shared fixtures for the minecraft test suite."""

from __future__ import annotations

from pathlib import Path

import pytest

DATA = Path(__file__).parent


@pytest.fixture
def sample_world() -> Path:
    """A real (tiny) Minecraft world: level.dat + one datapack."""
    return DATA / "world"


@pytest.fixture
def tmp_world(tmp_path: Path) -> Path:
    """A throwaway world folder with a couple of files and a nested datapack."""
    world = tmp_path / "world"
    (world / "region").mkdir(parents=True)
    (world / "level.dat").write_bytes(b"not-real-nbt")
    (world / "region" / "r.0.0.mca").write_bytes(b"chunkdata")
    (world / ".DS_Store").write_bytes(b"junk")
    return world
