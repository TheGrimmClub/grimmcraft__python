"""Shared fixtures: freshly compiled datapacks to decompile.

Tests compile their own fixtures with the real compiler rather than reading the
committed example packs, so the suite is hermetic and cannot drift out of sync
with the forward pipeline.  (The committed packs *are* exercised too, by
``test_roundtrip.py``, which is precisely where drift should be caught.)
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from grimmcraft_compiler.emit import emit
from grimmcraft_compiler.lower import lower
from grimmcraft_compiler.target import Target
from grimmcraft_control.demos import door_machine, furnace_machine
from grimmcraft_control.machine import Machine

#: The committed reference packs, used by the round-trip regression tests.
EXAMPLES = (
    Path(__file__).resolve().parents[2]
    / "grimmcraft-compiler"
    / "examples"
    / "generated"
)

#: Two versions either side of every behavioural threshold this package cares
#: about: plural folders + NBT item data (1.20.4) vs singular folders +
#: components + SNBT text (1.21.11).
VERSIONS = ("1.20.4", "1.21.11")


def build_pack(
    machines: list[Machine[Any]],
    destination: Path,
    version: str,
    *,
    namespace: str = "test",
    description: str | None = None,
) -> Path:
    """Compile ``machines`` into a datapack at ``destination``; return its path."""
    target = Target.resolve(version, "vanilla")
    text = description or f"{namespace} — grimmcraft datapack for {version} vanilla"
    pack = lower(machines, namespace, description=text)
    return emit(pack, target, destination)


@pytest.fixture
def demo_pack(tmp_path: Path) -> Path:
    """A two-machine (door + furnace) datapack for the newest supported version."""
    return build_pack([door_machine(), furnace_machine()], tmp_path / "demo", "1.21.11")


@pytest.fixture
def handwritten_pack(tmp_path: Path) -> Path:
    """A pack that follows no grimmcraft convention, with commands the IR can't model.

    Deliberately awkward: a rich ``tellraw`` component, a ``summon`` carrying NBT,
    a banner comment, a trailing space and a blank line — every shape that must
    survive as ``raw`` rather than be silently normalised.
    """
    root = tmp_path / "handwritten"
    functions = root / "data" / "custom" / "function"
    functions.mkdir(parents=True)
    (root / "pack.mcmeta").write_text(
        '{\n  "pack": {\n    "pack_format": 48,\n'
        '    "description": "A hand-written pack"\n  }\n}\n',
        encoding="utf-8",
    )
    (functions / "start.mcfunction").write_text(
        "### banner ###\n"
        'tellraw @a ["",{"text":"hi","color":"green"}]\n'
        "summon firework_rocket ~ ~1 ~ {LifeTime:45}\n"
        "scoreboard players remove timer custom 1 \n"
        "\n"
        "say plain command\n",
        encoding="utf-8",
    )
    (root / "data" / "minecraft" / "tags" / "function").mkdir(parents=True)
    (root / "data" / "minecraft" / "tags" / "function" / "load.json").write_text(
        '{"values": ["custom:start"]}\n', encoding="utf-8"
    )
    return root
