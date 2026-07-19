"""Tests for grimmclub_filesystem.archive (the Archive class + helpers).

These pin the *current* behaviour of the hand-written Archive class so future
changes are deliberate.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from grimmclub_filesystem.archive import Archive, StringChecker, is_valid_archive


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


# --- name and path as properties --------------------------------------------
def test_constructor_takes_a_path(tmp_path: Path):
    archive = Archive("backup.zip", tmp_path, do_cleanup=False)
    assert archive.path == tmp_path
    assert archive.full_path == tmp_path / "backup.zip"


def test_path_is_optional(tmp_path: Path):
    """Without a path an archive is just a name — which is all create() needs."""
    archive = Archive("backup.zip", do_cleanup=False)
    assert archive.path is None
    assert archive.full_path == Path("backup.zip")


def test_path_setter_coerces_a_string(tmp_path: Path):
    archive = Archive("backup.zip", do_cleanup=False)
    archive.path = str(tmp_path)
    assert isinstance(archive.path, Path), "a str must arrive as a SystemPath"
    assert archive.full_path == tmp_path / "backup.zip"


def test_name_setter_applies_the_same_cleaning_as_the_constructor():
    archive = Archive("first name!")
    assert archive.name == "firstname"
    archive.name = "second name!"
    assert archive.name == "secondname", "assignment must clean, not bypass"


def test_full_path_follows_both_parts(tmp_path: Path):
    """full_path is derived, so it cannot drift out of step with name and path."""
    archive = Archive("a.zip", tmp_path, do_cleanup=False)
    archive.name = "b.zip"
    assert archive.full_path == tmp_path / "b.zip"
    archive.path = tmp_path / "nested"
    assert archive.full_path == tmp_path / "nested" / "b.zip"


def test_create_records_where_it_wrote(tmp_path: Path):
    world = _make_world(tmp_path)
    archive = Archive("backup.zip", do_cleanup=False)
    archive.create(world, tmp_path / "out", do_date=False)
    assert archive.path == tmp_path / "out"
    assert archive.exists(), "the object now describes a real file"


# --- name validation ---------------------------------------------------------
def test_valid_name_accepts_a_clean_name():
    assert Archive("backup.zip", do_cleanup=False).is_valid_name() is True


def test_valid_name_rejects_forbidden_characters():
    archive = Archive("x", do_cleanup=False)
    for bad in ('a/b', 'a\\b', 'a:b', 'a*b', 'a?b', 'a"b', 'a<b', 'a>b', 'a|b'):
        assert archive.is_valid_name(bad) is False, bad


def test_valid_name_rejects_control_characters():
    assert Archive("x", do_cleanup=False).is_valid_name("a\x00b") is False


def test_valid_name_rejects_an_empty_name():
    assert Archive("x", do_cleanup=False).is_valid_name("") is False


def test_valid_name_rejects_windows_reserved_names():
    """CON and friends are refused whatever the extension."""
    archive = Archive("x", do_cleanup=False)
    assert archive.is_valid_name("con") is False
    assert archive.is_valid_name("CON.zip") is False
    assert archive.is_valid_name("lpt3.zip") is False
    assert archive.is_valid_name("console.zip") is True, "only exact names are reserved"


def test_valid_name_can_require_a_date():
    archive = Archive("x", do_cleanup=False)
    assert archive.is_valid_name("backup.zip", do_needs_date=True) is False
    assert archive.is_valid_name("backup__20260719.zip", do_needs_date=True) is True


def test_cleaning_a_name_of_pure_punctuation_still_yields_a_name():
    assert Archive("!!!").name == "archive"


def test_cleaning_refuses_to_produce_a_reserved_name():
    assert Archive("CON").name == "archive"


# --- dates -------------------------------------------------------------------
def test_append_date_keeps_the_extension_last():
    """`backup.zip__20260719` would no longer be recognisably a zip."""
    stamp = datetime.now().strftime("%Y%m%d")
    archive = Archive("backup.zip", do_cleanup=False)
    assert archive.append_date("backup.zip") == f"backup__{stamp}.zip"


def test_has_date_detects_the_stamp():
    assert Archive.has_date("backup__20260719.zip") is True
    assert Archive.has_date("backup.zip") is False
    assert Archive.has_date("backup__notadate.zip") is False


# --- extract -----------------------------------------------------------------
def test_extract_defaults_to_its_own_path(tmp_path: Path):
    world = _make_world(tmp_path)
    out = tmp_path / "out"
    Archive("backup.zip", do_cleanup=False).create(world, out, do_date=False)

    archive = Archive("backup.zip", out, do_cleanup=False)
    destination = archive.extract(to_path=tmp_path / "restored")
    assert (destination / "world" / "level.dat").is_file()


def test_extract_leaves_existing_files_alone_by_default(tmp_path: Path):
    world = _make_world(tmp_path)
    out = tmp_path / "out"
    Archive("backup.zip", do_cleanup=False).create(world, out, do_date=False)

    destination = tmp_path / "restored"
    (destination / "world").mkdir(parents=True)
    (destination / "world" / "level.dat").write_bytes(b"MINE")

    Archive("backup.zip", out, do_cleanup=False).extract(to_path=destination)
    assert (destination / "world" / "level.dat").read_bytes() == b"MINE"


def test_extract_overwrites_when_asked(tmp_path: Path):
    world = _make_world(tmp_path)
    out = tmp_path / "out"
    Archive("backup.zip", do_cleanup=False).create(world, out, do_date=False)

    destination = tmp_path / "restored"
    (destination / "world").mkdir(parents=True)
    (destination / "world" / "level.dat").write_bytes(b"MINE")

    Archive("backup.zip", out, do_cleanup=False).extract(
        to_path=destination, do_overwrite=True
    )
    assert (destination / "world" / "level.dat").read_bytes() == b"LEVEL"


# --- is_valid_archive --------------------------------------------------------
def test_is_valid_archive_accepts_a_real_archive(tmp_path: Path):
    world = _make_world(tmp_path)
    zip_path = Archive("backup.zip", do_cleanup=False).create(
        world, tmp_path / "out", do_date=False
    )
    assert is_valid_archive(zip_path) is True


def test_is_valid_archive_rejects_a_missing_file(tmp_path: Path):
    assert is_valid_archive(tmp_path / "nope.zip") is False


def test_is_valid_archive_rejects_a_file_that_is_not_a_zip(tmp_path: Path):
    """Existence is not enough — a truncated download exists."""
    impostor = tmp_path / "backup.zip"
    impostor.write_bytes(b"this is not a zip file")
    assert is_valid_archive(impostor) is False
