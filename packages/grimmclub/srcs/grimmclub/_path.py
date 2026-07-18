"""A :class:`Path` that is ``pathlib.Path`` plus debug logging of its I/O.

Same API as ``pathlib.Path`` — it *is* one — but every filesystem operation
emits a :func:`~grimmclub.log.debug` line when debug is enabled, so students can
see what their program reads and writes. Normal runs are silent. Path arithmetic
(``p / "sub"``) returns the same logging ``Path``, so the behaviour follows the
whole chain.
"""

from __future__ import annotations

import pathlib
from typing import IO, Any

from grimmclub.log import debug


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
        debug("open", self, args[0] if args else kwargs.get("mode", "r"))
        handle: IO[Any] = super().open(*args, **kwargs)
        return handle

    def mkdir(self, *args: Any, **kwargs: Any) -> None:
        debug("mkdir", self)
        return super().mkdir(*args, **kwargs)

    def unlink(self, *args: Any, **kwargs: Any) -> None:
        debug("unlink", self)
        return super().unlink(*args, **kwargs)
