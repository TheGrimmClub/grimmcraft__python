"""Version detection: pack_format → Target, narrowed by folders and description."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from grimmcraft_decompiler.detect import Confidence, detect_target
from grimmcraft_decompiler.diagnostics import Codes, DiagnosticBag
from grimmcraft_decompiler.source import open_pack


def write_pack(
    root: Path, mcmeta: dict[str, object], *, function_dir: str = "function"
) -> Path:
    """A minimal pack with the given metadata and folder scheme."""
    functions = root / "data" / "demo" / function_dir
    functions.mkdir(parents=True)
    (functions / "load.mcfunction").write_text("say hi\n", encoding="utf-8")
    (root / "pack.mcmeta").write_text(json.dumps(mcmeta), encoding="utf-8")
    return root


def detect(root: Path, **kwargs: object):
    bag = DiagnosticBag()
    with open_pack(root) as source:
        return detect_target(source, bag, **kwargs), bag  # type: ignore[arg-type]


def test_description_hint_pins_version_exactly(tmp_path: Path) -> None:
    """Format 48 is shared by 1.21 and 1.21.1 — only the description separates them."""
    root = write_pack(
        tmp_path / "p",
        {"pack": {"pack_format": 48, "description": "x — grimmcraft datapack for 1.21 vanilla"}},
    )
    detection, bag = detect(root)
    assert detection.target.version == "1.21"
    assert detection.confidence is Confidence.EXACT
    assert not list(bag)


def test_shared_pack_format_is_ambiguous(tmp_path: Path) -> None:
    root = write_pack(
        tmp_path / "p", {"pack": {"pack_format": 48, "description": "no hint here"}}
    )
    detection, bag = detect(root)
    assert detection.confidence is Confidence.AMBIGUOUS
    assert detection.candidates == ("1.21", "1.21.1")
    assert detection.target.version == "1.21.1", "assumes the newest candidate"
    assert Codes.AMBIGUOUS_VERSION in [d.code for d in bag]


def test_unique_pack_format_is_high_confidence(tmp_path: Path) -> None:
    root = write_pack(
        tmp_path / "p",
        {"pack": {"pack_format": 61, "description": "d"}},
    )
    detection, bag = detect(root)
    assert detection.target.version == "1.21.4"
    assert detection.confidence is Confidence.HIGH


def test_plural_folders_select_the_older_scheme(tmp_path: Path) -> None:
    root = write_pack(
        tmp_path / "p",
        {"pack": {"pack_format": 26, "description": "d"}},
        function_dir="functions",
    )
    detection, _ = detect(root)
    assert detection.target.version == "1.20.4"
    assert detection.singular_folders is False


def test_folder_scheme_contradicting_format_is_reported(tmp_path: Path) -> None:
    """Singular folders with a pre-1.21 format is a pack that disagrees with itself."""
    root = write_pack(
        tmp_path / "p",
        {"pack": {"pack_format": 26, "description": "d"}},
        function_dir="function",
    )
    _, bag = detect(root)
    assert Codes.FOLDER_SCHEME_MISMATCH in [d.code for d in bag]


def test_modern_min_format_is_read(tmp_path: Path) -> None:
    """1.21.9+ packs carry min_format/max_format instead of pack_format."""
    root = write_pack(
        tmp_path / "p",
        {"pack": {"min_format": [94, 1], "max_format": 94, "description": "d"}},
    )
    detection, _ = detect(root)
    assert detection.target.version == "1.21.11"


def test_unknown_pack_format_errors_but_still_returns_a_target(tmp_path: Path) -> None:
    root = write_pack(tmp_path / "p", {"pack": {"pack_format": 3, "description": "d"}})
    detection, bag = detect(root)
    assert Codes.UNKNOWN_PACK_FORMAT in [d.code for d in bag]
    assert detection.confidence is Confidence.FALLBACK
    assert detection.target is not None, "detection degrades, it does not abort"


def test_missing_pack_mcmeta_is_an_error(tmp_path: Path) -> None:
    root = tmp_path / "p"
    (root / "data" / "demo" / "function").mkdir(parents=True)
    detection, bag = detect(root)
    assert Codes.MISSING_PACK_MCMETA in [d.code for d in bag]
    assert detection.confidence is Confidence.FALLBACK


def test_invalid_json_is_an_error(tmp_path: Path) -> None:
    root = tmp_path / "p"
    (root / "data" / "demo" / "function").mkdir(parents=True)
    (root / "pack.mcmeta").write_text("{not json", encoding="utf-8")
    _, bag = detect(root)
    assert Codes.MISSING_PACK_MCMETA in [d.code for d in bag]


def test_version_override_wins(tmp_path: Path) -> None:
    root = write_pack(
        tmp_path / "p",
        {"pack": {"pack_format": 48, "description": "x for 1.21 vanilla"}},
    )
    detection, _ = detect(root, override="1.20.4")
    assert detection.target.version == "1.20.4"
    assert detection.confidence is Confidence.EXACT


def test_description_is_preserved_verbatim(tmp_path: Path) -> None:
    """The description is part of pack.mcmeta, so it must survive to re-emission."""
    description = "chess — grimmcraft datapack for 1.21.11 vanilla"
    root = write_pack(
        tmp_path / "p", {"pack": {"pack_format": 94, "description": description}}
    )
    detection, _ = detect(root)
    assert detection.description == description


def test_zip_archives_are_supported(tmp_path: Path) -> None:
    import shutil

    root = write_pack(tmp_path / "p", {"pack": {"pack_format": 61, "description": "d"}})
    archive = shutil.make_archive(str(tmp_path / "packed"), "zip", root_dir=root)
    detection, _ = detect(Path(archive))
    assert detection.target.version == "1.21.4"


def test_missing_input_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        open_pack(tmp_path / "nope")
