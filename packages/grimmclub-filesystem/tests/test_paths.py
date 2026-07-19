"""Path helpers, and the cross-platform junk detection."""

from __future__ import annotations

from pathlib import Path

import pytest

from grimmclub_filesystem.paths import (
    as_path,
    create_full_path,
    is_junk_directory,
    is_junk_path,
    junk_reason,
    locate_directory,
)


# --- as_path / create_full_path ----------------------------------------------
def test_as_path_expands_the_home_shorthand():
    assert as_path("~").is_absolute()


def test_create_full_path_makes_parents(tmp_path: Path):
    created = create_full_path(tmp_path / "a" / "b" / "c")
    assert created.is_dir()


def test_create_full_path_is_idempotent(tmp_path: Path):
    create_full_path(tmp_path / "a")
    assert create_full_path(tmp_path / "a").is_dir(), "must not raise on a second call"


# --- junk: macOS -------------------------------------------------------------
@pytest.mark.parametrize(
    "path",
    [".DS_Store", "a/b/.DS_Store", ".Spotlight-V100", ".Trashes", ".fseventsd",
     ".apdisk", ".AppleDouble", ".DocumentRevisions-V100"],
)
def test_macos_clutter_is_junk(path: str):
    assert is_junk_path(path), path


def test_apple_double_sidecars_are_matched_by_pattern():
    """`._notes.txt` varies with the file it shadows, so a name set cannot catch it."""
    assert junk_reason("x/._notes.txt") == "macOS AppleDouble resource fork"


def test_everything_inside_a_macosx_folder_is_junk():
    """The file's own name looks ordinary; where it sits is what condemns it."""
    assert is_junk_path("__MACOSX/deep/perfectly_normal.txt")


# --- junk: Windows -----------------------------------------------------------
@pytest.mark.parametrize(
    "path",
    ["Thumbs.db", "ehthumbs.db", "Desktop.ini", "$RECYCLE.BIN/f",
     "System Volume Information/tracking.log"],
)
def test_windows_clutter_is_junk(path: str):
    assert is_junk_path(path), path


def test_office_lock_files_are_junk():
    """Named after the document they lock, so this needs a pattern."""
    assert junk_reason("~$quarterly report.docx") == "Microsoft Office lock file"


def test_a_leading_tilde_is_not_expanded():
    """`~$report.docx` is a real file name, not a home-directory reference.

    `as_path` expands `~`, which is why the junk check deliberately does not
    use it — expanding here would raise or point somewhere absurd.
    """
    assert is_junk_path("~$report.docx")


# --- junk: Linux -------------------------------------------------------------
@pytest.mark.parametrize("path", [".directory", ".Trash", ".Trash-1000/x", ".Trash-0"])
def test_linux_clutter_is_junk(path: str):
    assert is_junk_path(path), path


def test_nfs_silly_rename_placeholders_are_junk():
    assert junk_reason(".nfs00000000012") is not None


# --- junk: editors and sync --------------------------------------------------
@pytest.mark.parametrize(
    "path", ["notes.txt~", ".notes.txt.swp", ".idea/workspace.xml", ".vscode/settings.json"]
)
def test_editor_clutter_is_junk(path: str):
    assert is_junk_path(path), path


def test_icloud_placeholders_are_junk():
    """A `.icloud` file is a stub — the real bytes have not been downloaded."""
    assert junk_reason("world.zip.icloud") is not None


# --- what must NOT be junk ---------------------------------------------------
@pytest.mark.parametrize(
    "path",
    ["world/level.dat", "data/pack.mcmeta", "src/main.py", "README.md",
     ".gitignore", ".github/workflows/ci.yml", "my.notes.txt"],
)
def test_real_files_are_kept(path: str):
    """False positives silently drop a user's data, so this list matters most."""
    assert not is_junk_path(path), path


def test_dot_git_is_not_junk():
    """Version control is not clutter — dropping it from an archive loses history."""
    assert not is_junk_path(".git/HEAD")


# --- the reason --------------------------------------------------------------
def test_reason_is_none_for_a_real_file():
    assert junk_reason("world/level.dat") is None


def test_reason_explains_rather_than_merely_refusing():
    assert junk_reason(".DS_Store") == "macOS Finder folder settings"


def test_the_old_name_still_works():
    """`is_junk_directory` is kept as an alias; callers already use it."""
    assert is_junk_directory is is_junk_path


# --- locate_directory --------------------------------------------------------
def test_locate_directory_finds_the_marker(tmp_path: Path):
    world = tmp_path / "saves" / "MyWorld"
    world.mkdir(parents=True)
    (world / "level.dat").write_bytes(b"x")
    assert locate_directory(tmp_path, "level.dat") == world


def test_locate_directory_skips_junk_copies(tmp_path: Path):
    """A world inside __MACOSX is an artefact of zipping, not a world."""
    junk = tmp_path / "__MACOSX" / "MyWorld"
    junk.mkdir(parents=True)
    (junk / "level.dat").write_bytes(b"x")
    assert locate_directory(tmp_path, "level.dat") is None


def test_locate_directory_returns_none_when_absent(tmp_path: Path):
    assert locate_directory(tmp_path, "level.dat") is None
