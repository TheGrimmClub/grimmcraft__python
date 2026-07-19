"""Tests for grimmclub_filesystem.archive (the Archive class + helpers).

These pin the *current* behaviour of the hand-written Archive class so future
changes are deliberate.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from grimmclub_filesystem.archive import Archive, StringChecker


def _make_world(root: Path) -> Path:
    world = root / "world"
    (world / "region").mkdir(parents=True)
    (world / "level.dat").write_bytes(b"LEVEL")
    (world / "region" / "r.0.0.mca").write_bytes(b"CHUNK")
    (world / ".DS_Store").write_bytes(b"junk")  # must be skipped
    return world


def test_create_and_extract_roundtrip(tmp_path: Path):
    world = _make_world(tmp_path)
    out = tmp_path / "out"

    zip_path = Archive("backup.zip", do_cleanup=False).create(world, out, do_date=False)
    assert zip_path == out / "backup.zip"
    assert zip_path.is_file()

    dest = tmp_path / "restored"
    Archive("backup.zip", do_cleanup=False).extract(zip_path, dest)

    assert (dest / "world" / "level.dat").read_bytes() == b"LEVEL"
    assert (dest / "world" / "region" / "r.0.0.mca").is_file()
    assert not (dest / "world" / ".DS_Store").exists()  # junk was skipped


def test_list_skips_junk(tmp_path: Path):
    world = _make_world(tmp_path)
    out = tmp_path / "out"
    archive = Archive("backup.zip", do_cleanup=False)
    zip_path = archive.create(world, out, do_date=False)

    names = archive.list(zip_path)
    assert any(name.endswith("level.dat") for name in names)
    assert all(".DS_Store" not in name for name in names)


def test_append_date_format():
    stamp = datetime.now().strftime("%Y%m%d")
    assert Archive("base", do_cleanup=False).append_date("base") == f"base__{stamp}"


def test_valid_name_normalises():
    # spaces -> _, special chars (incl. '_' '.' '!') removed, then lower-cased
    assert Archive("My World! v1.2").name == "myworldv12"
    assert Archive("").name == "archive"


def test_string_checker_space_cleaner():
    checker = StringChecker()
    assert checker.space_cleaner("a b-c") == "a__b_c"
