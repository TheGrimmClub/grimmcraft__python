"""Small teaching helpers: friendly logging, debug tracing and output banners.

These are the "extra help" a facade over the stdlib gives you — a single place to
add output that helps students see what their code is doing, without changing the
stdlib APIs themselves.
"""

from __future__ import annotations

import os
import sys
from typing import Any

_TRUTHY = {"1", "true", "yes", "on"}

#: Whether :func:`debug` prints. Starts on when ``GRIMMCLUB_DEBUG`` is truthy.
_debug_enabled: bool = os.environ.get("GRIMMCLUB_DEBUG", "").lower() in _TRUTHY


def set_debug(enabled: bool) -> None:
    """Turn :func:`debug` output on or off at runtime."""
    global _debug_enabled
    _debug_enabled = enabled


def debug_enabled() -> bool:
    """Whether :func:`debug` is currently printing."""
    return _debug_enabled


def log(*values: Any, sep: str = " ") -> None:
    """Print ``values`` to stderr, prefixed with ``[grimmclub]``.

    Use it like :func:`print`; it goes to stderr so it never mixes into a
    program's real output.
    """
    print("[grimmclub]", sep.join(str(v) for v in values), file=sys.stderr)


def debug(*values: Any, sep: str = " ") -> None:
    """Like :func:`log`, but only prints when debug is enabled.

    Enable it with ``GRIMMCLUB_DEBUG=1`` in the environment or
    ``set_debug(True)``. Handy for tracing a program without deleting the lines
    afterwards.
    """
    if _debug_enabled:
        print("[grimmclub:debug]", sep.join(str(v) for v in values), file=sys.stderr)


def banner(title: str, *, width: int = 60, char: str = "=") -> None:
    """Print a centred, titled separator line — structure your script's output.

    ``banner("Results")`` →  ``========================= Results =========================``
    """
    print(f" {title} ".center(width, char))
