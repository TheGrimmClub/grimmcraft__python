"""Tests for grimmclub_filesystem.core — the shared aliases and StringChecker."""

from __future__ import annotations

import pathlib

from grimmclub_filesystem.core import (
    ZIP_DEFLATED,
    BadZipFile,
    StringChecker,
    SystemPath,
    ZipFile,
    get_iso_date,
    get_iso_time,
    is_zipfile,
    no,
    yes,
)


# --- the re-exports ----------------------------------------------------------
def test_core_is_the_single_point_of_contact_with_the_standard_library():
    """The premise of the package: siblings import these from here, not stdlib."""
    assert SystemPath is pathlib.Path
    assert ZipFile.__module__ == "zipfile"
    assert BadZipFile.__module__ == "zipfile"
    assert callable(is_zipfile)
    assert isinstance(ZIP_DEFLATED, int)


def test_boolean_constants_read_as_english():
    assert yes is True
    assert no is False


# --- dates -------------------------------------------------------------------
def test_iso_date_is_eight_digits():
    stamp = get_iso_date()
    assert len(stamp) == 8 and stamp.isdigit()


def test_iso_time_is_date_underscore_time():
    stamp = get_iso_time()
    date_part, _, time_part = stamp.partition("_")
    assert len(date_part) == 8 and date_part.isdigit()
    assert len(time_part) == 6 and time_part.isdigit()


def test_iso_time_starts_with_the_iso_date():
    assert get_iso_time().startswith(get_iso_date())


# --- StringChecker -----------------------------------------------------------
def test_space_cleaner_replaces_spaces_with_a_double_underscore():
    assert StringChecker().space_cleaner("a b") == "a__b"


def test_space_cleaner_replaces_hyphens_with_one_underscore():
    assert StringChecker().space_cleaner("a-b") == "a_b"


def test_space_cleaner_handles_both_at_once():
    assert StringChecker().space_cleaner("my world-01 backup") == "my__world_01__backup"


def test_space_cleaner_leaves_a_clean_name_alone():
    assert StringChecker().space_cleaner("already_clean") == "already_clean"


def test_special_chars_covers_the_shell_metacharacters():
    """These are what make a name unsafe to paste into a command."""
    special = StringChecker().special_chars
    for character in r"""!@#$%^&*()|\;"'<>?`""":
        assert character in special, character


def test_special_chars_includes_the_dot():
    """Documented consequence: cleaning a name removes its extension.

    `Archive.get_valid_name("backup.zip")` yields "backupzip". That is fine for
    a label and wrong for a filename, which is why `Archive` is constructed with
    `do_cleanup=False` wherever a real file name matters.
    """
    assert "." in StringChecker().special_chars


def test_each_checker_gets_its_own_set():
    """The set is per-instance, so one caller cannot mutate another's rules."""
    first, second = StringChecker(), StringChecker()
    first.special_chars.add("§")
    assert "§" not in second.special_chars
