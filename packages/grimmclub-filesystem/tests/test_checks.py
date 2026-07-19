"""The guards, and the FileType they can demand."""

from __future__ import annotations

import zipfile
from pathlib import Path

import pytest

from grimmclub_filesystem.checks import (
    ContentError,
    FileType,
    expect,
    expect_directory,
    expect_file,
    expect_json,
    expect_json_object,
)


def make_archive(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("hello.txt", "hi")
    return path


# --- expect_file -------------------------------------------------------------
def test_missing_file_names_the_folder_when_it_is_absent(tmp_path: Path):
    with pytest.raises(FileNotFoundError, match="does not exist"):
        expect_file(tmp_path / "nowhere" / "thing.txt")


def test_missing_file_suggests_a_close_sibling(tmp_path: Path):
    (tmp_path / "room.nbt").write_bytes(b"x")
    with pytest.raises(FileNotFoundError, match="did you mean 'room.nbt'"):
        expect_file(tmp_path / "rom.nbt")


def test_a_directory_is_reported_as_such(tmp_path: Path):
    with pytest.raises(IsADirectoryError):
        expect_file(tmp_path)


def test_empty_file_rejected_when_asked(tmp_path: Path):
    empty = tmp_path / "empty.txt"
    empty.touch()
    assert expect_file(empty) == empty, "allowed by default"
    with pytest.raises(ContentError, match="is empty"):
        expect_file(empty, allow_empty=False)


# --- FileType ----------------------------------------------------------------
def test_bands_classify_the_members():
    assert FileType.DIRECTORY.is_structural
    assert FileType.MARKDOWN.is_text
    assert FileType.ARCHIVE.is_binary
    assert not FileType.ARCHIVE.is_text


def test_archive_is_matched_by_content_not_by_name(tmp_path: Path):
    """The whole point: a .zip that is not a zip must be rejected."""
    real = make_archive(tmp_path / "real.zip")
    impostor = tmp_path / "impostor.zip"
    impostor.write_bytes(b"definitely not a zip")

    assert FileType.ARCHIVE.matches(real) is True
    assert FileType.ARCHIVE.matches(impostor) is False


def test_text_is_matched_by_decodability(tmp_path: Path):
    text = tmp_path / "notes.txt"
    text.write_text("hello", encoding="utf-8")
    binary = tmp_path / "blob.bin"
    binary.write_bytes(b"\x00\x01\x02")

    assert FileType.TEXT.matches(text) is True
    assert FileType.TEXT.matches(binary) is False
    assert FileType.BINARY.matches(binary) is True


def test_nul_byte_means_binary_even_if_it_decodes(tmp_path: Path):
    sneaky = tmp_path / "sneaky.txt"
    sneaky.write_bytes(b"looks like text\x00but is not")
    assert FileType.TEXT.matches(sneaky) is False


def test_markdown_is_matched_by_suffix(tmp_path: Path):
    note = tmp_path / "note.md"
    note.write_text("# hi", encoding="utf-8")
    other = tmp_path / "note.txt"
    other.write_text("# hi", encoding="utf-8")

    assert FileType.MARKDOWN.matches(note) is True
    assert FileType.MARKDOWN.matches(other) is False


def test_expect_file_enforces_the_type(tmp_path: Path):
    impostor = tmp_path / "pack.zip"
    impostor.write_bytes(b"truncated download")
    with pytest.raises(ContentError, match="not a valid archive"):
        expect_file(impostor, what="datapack", file_type=FileType.ARCHIVE)


def test_expect_file_accepts_a_matching_type(tmp_path: Path):
    real = make_archive(tmp_path / "pack.zip")
    assert expect_file(real, file_type=FileType.ARCHIVE) == real


# --- expect() dispatcher -----------------------------------------------------
def test_expect_dispatches_to_directory(tmp_path: Path):
    assert expect(FileType.DIRECTORY, tmp_path) == tmp_path


def test_expect_dispatches_to_archive(tmp_path: Path):
    real = make_archive(tmp_path / "pack.zip")
    assert expect(FileType.ARCHIVE, real) == real


def test_expect_rejects_a_mismatch(tmp_path: Path):
    note = tmp_path / "note.md"
    note.write_text("# hi", encoding="utf-8")
    with pytest.raises(ContentError):
        expect(FileType.ARCHIVE, note)


def test_expect_treats_empty_text_as_a_failure(tmp_path: Path):
    """A zero-byte Markdown file is a failed write, not a deliberate blank."""
    empty = tmp_path / "note.md"
    empty.touch()
    with pytest.raises(ContentError, match="is empty"):
        expect(FileType.MARKDOWN, empty)


# --- json --------------------------------------------------------------------
def test_bad_json_quotes_the_offending_line(tmp_path: Path):
    broken = tmp_path / "pack.mcmeta"
    broken.write_text('{\n  "pack": {\n    "x": 1\n    "y": 2\n  }\n}', encoding="utf-8")
    with pytest.raises(ContentError, match="line 4"):
        expect_json(broken)


def test_json_object_rejects_a_bare_list(tmp_path: Path):
    listed = tmp_path / "values.json"
    listed.write_text("[1, 2, 3]", encoding="utf-8")
    with pytest.raises(ContentError, match="holds a list"):
        expect_json_object(listed)


def test_expect_directory_rejects_a_file(tmp_path: Path):
    target = tmp_path / "thing.txt"
    target.write_text("x", encoding="utf-8")
    with pytest.raises(NotADirectoryError):
        expect_directory(target)


# --- YAML (layer three) ------------------------------------------------------
def test_yaml_document_is_parsed(tmp_path: Path):
    path = tmp_path / "config.yaml"
    path.write_text("town:\n  port: 8080\n", encoding="utf-8")
    from grimmclub_filesystem.checks import expect_yaml_document

    assert expect_yaml_document(path) == {"town": {"port": 8080}}


def test_bad_yaml_reports_the_line(tmp_path: Path):
    """The suffix check cannot catch this — only parsing can."""
    from grimmclub_filesystem.checks import expect_yaml_document

    path = tmp_path / "config.yaml"
    path.write_text("town:\n  port: 8080\n bad indent here\n", encoding="utf-8")
    with pytest.raises(ContentError, match="not valid YAML"):
        expect_yaml_document(path)


def test_yaml_mapping_rejects_a_bare_list(tmp_path: Path):
    from grimmclub_filesystem.checks import expect_yaml_mapping

    path = tmp_path / "config.yaml"
    path.write_text("- one\n- two\n", encoding="utf-8")
    with pytest.raises(ContentError, match="should hold a YAML mapping"):
        expect_yaml_mapping(path)


def test_yaml_suffix_guard_does_not_parse(tmp_path: Path):
    """Layer two checks the name; layer three checks the content."""
    from grimmclub_filesystem.checks import expect_yaml

    path = tmp_path / "config.yaml"
    path.write_text("this: is: not: valid: yaml\n", encoding="utf-8")
    assert expect_yaml(path) == path, "the suffix guard is satisfied"
