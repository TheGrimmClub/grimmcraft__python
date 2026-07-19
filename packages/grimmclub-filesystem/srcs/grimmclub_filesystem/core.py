
# Includes standard
# This module is the package's single point of contact with the standard
# library: the sibling modules import these names *from here* rather than
# reaching for `zipfile` or `pathlib` themselves, which is the whole premise of
# the package. They are therefore deliberate re-exports, not unused imports.
from __future__ import annotations

from datetime import datetime as DateTime
from pathlib import Path as SystemPath
from typing import Any
from zipfile import ZIP_DEFLATED, BadZipFile, ZipFile, is_zipfile

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
# - Boolean
yes = True
true = True

no = False
false = False

# Classes
#
class StringChecker:
    """A simple string checker for archive names.
    TODO: create tests
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
