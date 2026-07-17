"""End-to-end: compile the demo machines to a datapack and verify it loads."""

from __future__ import annotations

import json
import zipfile
from pathlib import Path

import pytest

from grimmcraft_compiler import Target, compile_machines
from grimmcraft_control.demos import door_machine, furnace_machine

VERSIONS = ["1.20.4", "1.21.1"]
FLAVORS = ["vanilla", "paper", "fabric"]


@pytest.mark.parametrize("version", VERSIONS)
@pytest.mark.parametrize("flavor", FLAVORS)
def test_compile_demos_end_to_end(version: str, flavor: str, tmp_path: Path) -> None:
    target = Target.resolve(version, flavor)
    out = tmp_path / "pack"
    result = compile_machines(
        [door_machine(), furnace_machine()], target,
        namespace="grimmcraft", output=out,
    )

    # No errors, and the pack was written and verified.
    assert result.ok, [d.message for d in result.diagnostics.errors]
    assert result.emitted
    assert result.output_path == out

    # pack.mcmeta has the right pack_format and is valid JSON.
    meta = json.loads((out / "pack.mcmeta").read_text())
    assert meta["pack"]["pack_format"] == target.info.pack_format

    # Folder scheme matches the version.
    fdir = "function" if target.info.singular_folders else "functions"
    wrong = "functions" if target.info.singular_folders else "function"
    assert (out / "data" / "grimmcraft" / fdir).is_dir()
    assert not (out / "data" / "grimmcraft" / wrong).exists()

    # Every JSON resource parses.
    for json_file in out.rglob("*.json"):
        json.loads(json_file.read_text())

    # Load and tick tags exist and point at real functions.
    tag = json.loads((out / "data/minecraft/tags" / fdir / "load.json").read_text())
    assert "grimmcraft:load" in tag["values"]


@pytest.mark.parametrize("version", VERSIONS)
def test_all_function_calls_resolve(version: str, tmp_path: Path) -> None:
    target = Target.resolve(version, "vanilla")
    out = tmp_path / "pack"
    compile_machines([door_machine(), furnace_machine()], target,
                     namespace="grimmcraft", output=out)

    fdir = "function" if target.info.singular_folders else "functions"
    root = out / "data" / "grimmcraft" / fdir
    defined = {
        f"grimmcraft:{p.relative_to(root).with_suffix('').as_posix()}"
        for p in root.rglob("*.mcfunction")
    }
    for mcfunction in root.rglob("*.mcfunction"):
        for line in mcfunction.read_text().splitlines():
            stripped = line.strip()
            if " function " in f" {stripped} ":
                ref = stripped.split("function", 1)[1].strip()
                assert ref in defined, f"{mcfunction.name} calls missing {ref}"


def test_zip_output(tmp_path: Path) -> None:
    target = Target.resolve("1.21.1", "vanilla")
    out = tmp_path / "pack"
    result = compile_machines([door_machine()], target, output=out, zip_output=True)
    assert result.output_path is not None
    assert result.output_path.suffix == ".zip"
    with zipfile.ZipFile(result.output_path) as zf:
        assert "pack.mcmeta" in zf.namelist()


def test_errors_block_emission_unless_forced(tmp_path: Path) -> None:
    from typing import Any

    from grimmcraft_control.machine import Command, MachineBuilder

    bad = (
        MachineBuilder[dict[str, Any]]({})
        .named("bad")
        .state("A").state("B")
        .transition("A", "go", to="B",
                    commands=(Command("setblock",
                                      {"pos": (0, 0, 0), "block": "minecraft:nope"}),))
        .initial("A").build()
    )
    target = Target.resolve("1.21.1", "vanilla")

    blocked = compile_machines([bad], target, output=tmp_path / "a")
    assert not blocked.emitted and not blocked.ok

    forced = compile_machines([bad], target, output=tmp_path / "b", force=True)
    assert forced.emitted  # emitted despite the error
