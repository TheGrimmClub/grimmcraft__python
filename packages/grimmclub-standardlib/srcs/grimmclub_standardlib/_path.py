"""A :class:`Path` that is ``pathlib.Path`` plus debug logging of its I/O.

Same API as ``pathlib.Path`` — it *is* one — but every filesystem operation
emits a :func:`~grimmclub.log.debug` line when debug is enabled, so students can
see what their program reads and writes. Normal runs are silent. Path arithmetic
(``p / "sub"``) returns the same logging ``Path``, so the behaviour follows the
whole chain.

# Classes:
- Path: for directories, files and links

Methods carry both spellings: pathlib's (``open``, ``mkdir``) because the
standard library calls them internally, and the explicit house names
(``open_file``, ``create_directory``) as aliases onto the same logging code.
"""

from __future__ import annotations

import pathlib
from typing import IO, Any

from grimmclub_standardlib.log import debug


class Path(pathlib.Path):
    """``pathlib.Path`` that debug-logs the filesystem operations it performs."""

    def read_text(self, *args: Any, **kwargs: Any) -> str:
        debug("read_text", self)
        return super().read_text(*args, **kwargs)

    def write_text(self, data: str, *args: Any, **kwargs: Any) -> int:
        debug("write_text", self, f"({len(data)} chars)")
        return super().write_text(data, *args, **kwargs)

    def read_bytes(self) -> bytes:
        debug("read_bytes", self)
        return super().read_bytes()

    def write_bytes(self, data: Any) -> int:
        debug("write_bytes", self, f"({len(data)} bytes)")
        return super().write_bytes(data)

    def open(self, *args: Any, **kwargs: Any) -> IO[Any]:  # type: ignore[override]
        debug("open file", self, args[0] if args else kwargs.get("mode", "r"))
        handle: IO[Any] = super().open(*args, **kwargs)
        return handle

    def mkdir(self, *args: Any, **kwargs: Any) -> None:
        debug("make directory", self)
        return super().mkdir(*args, **kwargs)

    # The house style prefers explicit names, and ``create_directory`` /
    # ``open_file`` are the ones to teach. They must be *aliases* rather than
    # replacements: ``pathlib`` calls ``self.open()`` and ``self.mkdir()``
    # internally (``write_text`` goes through ``open``, ``mkdir(parents=True)``
    # recurses through ``mkdir``), so dropping those names does not rename the
    # operation -- it silently stops logging the two things students do most,
    # while both names keep working. Same reasoning for remove_file/rmdir.
    open_file = open
    create_directory = mkdir

    def unlink(self, *args: Any, **kwargs: Any) -> None:
        debug("remove file", self)
        return super().unlink(*args, **kwargs)

    def rmdir(self) -> None:
        debug("remove directory", self)
        return super().rmdir()

    remove_file = unlink
    remove_directory = rmdir
