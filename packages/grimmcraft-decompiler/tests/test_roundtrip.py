"""The round-trip contract — the package's central correctness property.

``compile(decompile(pack)) == pack``, byte for byte, for every pack the compiler
produced.  These tests run it two ways:

* over **freshly compiled** packs, which keeps the suite hermetic; and
* over the **committed example packs**, which is where drift between the two
  directions of the pipeline shows up first.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from grimmcraft_control.demos import door_machine, furnace_machine
from grimmcraft_decompiler import decompile, open_pack, roundtrip
from grimmcraft_decompiler.roundtrip import Level

from .conftest import EXAMPLES, VERSIONS, build_pack

#: Every committed reference pack, by directory name.
EXAMPLE_PACKS = sorted(
    (path.name for path in EXAMPLES.iterdir() if path.is_dir() and any(path.iterdir())),
) if EXAMPLES.is_dir() else []


def check(path: Path, *, level: Level) -> None:
    """Decompile ``path``, re-emit at ``level``, and demand byte equality."""
    result = decompile(path, emit="machine" if level is Level.MACHINE else "ir")
    with result.source:
        report = roundtrip(
            result.source,
            result.pack,
            result.target,
            machines=result.machines or None,
            level=level,
        )
        assert report.identical, report.render()


@pytest.mark.parametrize("version", VERSIONS)
def test_ir_roundtrip_of_fresh_pack(tmp_path: Path, version: str) -> None:
    pack = build_pack([door_machine(), furnace_machine()], tmp_path / "p", version)
    check(pack, level=Level.IR)


@pytest.mark.parametrize("version", VERSIONS)
def test_machine_roundtrip_of_fresh_pack(tmp_path: Path, version: str) -> None:
    """The strict claim: reconstructed machines re-lower to the same bytes."""
    pack = build_pack([door_machine(), furnace_machine()], tmp_path / "p", version)
    check(pack, level=Level.MACHINE)


@pytest.mark.skipif(not EXAMPLE_PACKS, reason="no committed example packs")
@pytest.mark.parametrize("name", EXAMPLE_PACKS)
def test_ir_roundtrip_of_committed_examples(name: str) -> None:
    check(EXAMPLES / name, level=Level.IR)


@pytest.mark.skipif(not EXAMPLE_PACKS, reason="no committed example packs")
@pytest.mark.parametrize("name", EXAMPLE_PACKS)
def test_machine_roundtrip_of_committed_examples(name: str) -> None:
    check(EXAMPLES / name, level=Level.MACHINE)


@pytest.mark.skipif(not EXAMPLE_PACKS, reason="no committed example packs")
def test_committed_examples_span_several_versions() -> None:
    """The guarantee is only meaningful if the fixtures cross a version threshold."""
    versions = set()
    for name in EXAMPLE_PACKS:
        result = decompile(EXAMPLES / name, emit="ir")
        with result.source:
            versions.add(result.target.version)
    assert len(versions) >= 2, f"examples only cover {versions}"


@pytest.mark.parametrize("version", VERSIONS)
def test_zipped_pack_roundtrips(tmp_path: Path, version: str) -> None:
    import shutil

    pack = build_pack([door_machine()], tmp_path / "p", version)
    archive = shutil.make_archive(str(tmp_path / "packed"), "zip", root_dir=pack)
    check(Path(archive), level=Level.MACHINE)


def test_handwritten_pack_roundtrips_structurally(handwritten_pack: Path) -> None:
    """Hand-written packs keep the weaker guarantee: content survives, layout may not.

    Every ``.mcfunction`` must still reproduce exactly — that is what "nothing is
    lost" means — while JSON indentation and the added ``supported_formats`` band
    are allowed to differ.
    """
    result = decompile(handwritten_pack, emit="ir")
    with result.source:
        report = roundtrip(
            result.source, result.pack, result.target, strict=False
        )
        offenders = [d for d in report.differences if d.path.endswith(".mcfunction")]
        assert not offenders, report.render()


def test_roundtrip_flag_reports_a_mismatch(tmp_path: Path) -> None:
    """A pack edited after compilation must be reported, not silently accepted."""
    pack = build_pack([door_machine()], tmp_path / "p", "1.21.11")
    stray = pack / "data" / "test" / "function" / "extra.mcfunction"
    stray.write_text("say not part of any machine\n", encoding="utf-8")

    result = decompile(pack, emit="machine", check_roundtrip=True)
    with result.source:
        assert result.diff is not None
        assert not result.diff.identical
        assert any(d.path.endswith("extra.mcfunction") for d in result.diff.differences)


def test_diff_report_summary_is_readable(tmp_path: Path) -> None:
    pack = build_pack([door_machine()], tmp_path / "p", "1.21.11")
    with open_pack(pack) as source:
        result = decompile(pack, emit="ir")
        report = roundtrip(source, result.pack, result.target)
        assert "identical" in report.summary()
        assert str(result.target) in report.summary()
