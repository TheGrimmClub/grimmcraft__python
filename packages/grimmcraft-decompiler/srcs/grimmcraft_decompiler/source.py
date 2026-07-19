"""Loading a datapack off disk — a directory or a ``.zip`` — as a file map.

:func:`open_pack` normalises both shapes into a :class:`PackSource`: the pack
root plus every file's text, keyed by its POSIX-style path relative to the root.
A ``.zip`` is extracted into a temporary directory that lives for as long as the
:class:`PackSource` is used as a context manager.

Packs are sometimes zipped with a single top-level folder wrapping the real root
(``mypack.zip`` → ``mypack/pack.mcmeta``); :func:`open_pack` descends into it so
callers always see the directory that *contains* ``pack.mcmeta``.
"""

from __future__ import annotations

import tempfile
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from types import TracebackType

from grimmclub_filesystem.archive import extract_archive

#: The marker file that identifies a datapack root.
PACK_META = "pack.mcmeta"


@dataclass(slots=True)
class PackSource:
    """A loaded datapack: its root and every file's text content.

    ``files`` maps a relative POSIX path (``"data/ns/function/load.mcfunction"``)
    to the file's decoded text.  Binary files that are not valid UTF-8 are
    skipped — a datapack is text, and a stray ``.DS_Store`` should not abort a
    decompile.
    """

    root: Path
    files: dict[str, str] = field(default_factory=dict)
    #: Set when the source was extracted from an archive (cleaned up on exit).
    _tempdir: tempfile.TemporaryDirectory[str] | None = None
    #: The original argument the user passed (a dir or a .zip), for diagnostics.
    origin: Path | None = None

    def __enter__(self) -> PackSource:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.close()

    def close(self) -> None:
        """Remove the temporary extraction directory, if there was one."""
        if self._tempdir is not None:
            self._tempdir.cleanup()
            self._tempdir = None

    @property
    def label(self) -> str:
        """A short name for this pack, used in diagnostics and generated docs."""
        return (self.origin or self.root).name

    def read(self, relative: str) -> str | None:
        """The text of ``relative``, or ``None`` when the pack has no such file."""
        return self.files.get(relative)

    def paths_under(self, prefix: str, suffix: str = "") -> list[str]:
        """Every file path starting with ``prefix`` and ending with ``suffix``.

        Sorted, so downstream lifting is deterministic regardless of how the
        filesystem or archive happened to order its entries.
        """
        return sorted(
            path
            for path in self.files
            if path.startswith(prefix) and path.endswith(suffix)
        )

    @property
    def namespaces(self) -> list[str]:
        """Every namespace directory under ``data/``, sorted."""
        found = {
            parts[1]
            for path in self.files
            if len(parts := path.split("/")) > 2 and parts[0] == "data"
        }
        return sorted(found)


def _read_tree(root: Path) -> dict[str, str]:
    """Every UTF-8 readable file under ``root``, keyed by relative POSIX path."""
    files: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue  # not text (or unreadable) — not part of a datapack
        files[path.relative_to(root).as_posix()] = text
    return files


def _descend_to_root(root: Path) -> Path:
    """Follow a single wrapping directory down to the one holding ``pack.mcmeta``."""
    if (root / PACK_META).is_file():
        return root
    entries = [p for p in root.iterdir() if not p.name.startswith(".")]
    if len(entries) == 1 and entries[0].is_dir() and (entries[0] / PACK_META).is_file():
        return entries[0]
    return root


def open_pack(path: Path | str) -> PackSource:
    """Load the datapack at ``path`` — a directory or a ``.zip`` archive.

    Raises :class:`FileNotFoundError` if the path does not exist and
    :class:`ValueError` for a file that is not a readable ``.zip``.  A *missing*
    ``pack.mcmeta`` is **not** an error here — it is reported as the ``GD1002``
    diagnostic during decompilation, so the caller still gets a report.
    """
    origin = Path(path)
    if not origin.exists():
        raise FileNotFoundError(f"no such datapack: {origin}")

    if origin.is_dir():
        root = _descend_to_root(origin)
        return PackSource(root=root, files=_read_tree(root), origin=origin)

    if not zipfile.is_zipfile(origin):
        raise ValueError(
            f"{origin} is neither a directory nor a .zip archive; "
            "point at a datapack folder or its zipped form"
        )

    tempdir = tempfile.TemporaryDirectory(prefix="grimmcraft-decompile-")
    # Via grimmclub-filesystem so the macOS junk (__MACOSX, .DS_Store) that a
    # Finder-zipped pack carries is skipped on the way in.
    extract_archive(origin, tempdir.name)
    root = _descend_to_root(Path(tempdir.name))
    return PackSource(
        root=root, files=_read_tree(root), _tempdir=tempdir, origin=origin
    )
