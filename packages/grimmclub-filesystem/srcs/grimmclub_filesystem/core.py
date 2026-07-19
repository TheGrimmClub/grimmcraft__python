"""
This module is the package's single point of contact with the standard library
for *file* things: the sibling modules import `SystemPath`, `ZipFile` and the
rest from here rather than reaching for `pathlib` or `zipfile` themselves,
which is the whole premise of the package. They are deliberate re-exports, not
unused imports.

The house vocabulary — `yes`/`no`/`true`/`false` and `Any` — is **not** defined
here. It comes from `grimmclub_standardlib`, which sits below this package, so
that there is one definition of `yes` in the workspace rather than two that can
drift apart.

Note that `SystemPath` is plain `pathlib.Path`, *not* `grimmclub.Path`. The
latter debug-logs every read and write, which is right for a lesson and wrong
for a backup tool that copies thousands of files.
"""
from __future__ import annotations

from datetime import datetime as DateTime
from zipfile import ZIP_DEFLATED, BadZipFile, ZipFile, is_zipfile

# The shared vocabulary, defined once at the bottom of the stack.
from grimmclub_standardlib import Any, SystemPath, false, no, true, yes

# Re-exported on purpose (see above) — naming them here tells both ruff and
# mypy that these are part of this module's public surface.
__all__ = [
    "Any",
    "SystemPath",
    "ZIP_DEFLATED",
    "BadZipFile",
    "is_zipfile",
    "ZipFile",
    "AnyOptional",
    "StringChecker",
    "SystemPathOptional",
    "false",
    "get_iso_date",
    "get_iso_time",
    "no",
    "path_like",
    "path_like_optional",
    "true",
    "yes",
]

# Types
path_like = str | SystemPath
path_like_optional = path_like | None
SystemPathOptional = SystemPath | None
AnyOptional = Any | None

# Constants

# Classes
#
class StringChecker:
    """A simple string checker for archive names.

    Holds the set of characters :meth:`Archive.get_valid_name` strips, and the
    space-to-underscore rule used when a name has to survive a shell or a URL.

    Note that ``special_chars`` includes ``.``, so cleaning a name removes its
    extension — ``backup.zip`` becomes ``backupzip``. That is deliberate for a
    *label*, but callers naming an actual file should keep the suffix
    themselves; see ``tests/test_core.py``.
    """
    def __init__(self) -> None:
        self.special_chars : set[str] = set("!@#$%^&*()_+{}[]|\\:;\"'<>,.?/~`")

    def space_cleaner(self, name: str) -> str:
        return str(name.replace(" ", "__").replace('-', '_'))


# Functions
#
def get_iso_time() -> str:
    """wrapper to get the ISO time string (YYYYMMDD_HHMMSS)
    """
    return DateTime.now().strftime('%Y%m%d_%H%M%S')

def get_iso_date() -> str:
    """wrapper to get the ISO date string (YYYYMMDD)
    """
    return DateTime.now().strftime('%Y%m%d')
