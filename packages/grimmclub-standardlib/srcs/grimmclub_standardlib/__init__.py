"""grimmclub-standardlib — a curated facade over the Python standard library.

One place to import the everyday "batteries" from, with the **same names and
APIs** as the stdlib, plus the teaching helpers that make a program's work
visible (:func:`log`, :func:`debug`, :func:`banner`).

Two shapes are re-exported:

* **common leaf names** used directly (``Path``, ``dataclass``, ``StrEnum``,
  ``Any``, ``datetime`` …) — because that is how they are normally imported;
* **whole modules** (``os``, ``sys``, ``json``, ``math``, ``random``,
  ``itertools``, ``textwrap``) — because their members (``json.dumps``,
  ``os.getcwd``) collide if flattened, and ``module.member`` reads clearest.

Some names are genuinely **wrapped**, which is how the facade earns its keep:
``Path`` and ``json`` are drop-in replacements that debug-log their I/O (see
:mod:`._path` / :mod:`._json`). The rest are plain re-exports — wrap more the
same way when a lesson calls for it.

This package sits at the **bottom** of the grimmclub stack: it has no
dependencies, and everything else may rely on it. Trainees do not import it
directly — they import :mod:`grimmclub`, which re-exports all of this alongside
the other libraries. It is separate so that a working library such as
``grimmclub-filesystem`` can share the house vocabulary (``yes``/``no``,
``debug``) without depending on the whole teaching front door.
"""

from __future__ import annotations

# --- whole modules (use as `os.getcwd()`, `math.pi`, …) ----------------------
import itertools
import math
import os
import random
import sys
import textwrap

# --- common leaf names (imported directly in normal code) --------------------
from collections import Counter, defaultdict, deque
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from enum import Enum, IntEnum, StrEnum, auto
from pathlib import Path as SystemPath
from typing import IO, TYPE_CHECKING, Any, BinaryIO, Optional, Protocol, TextIO

from grimmclub_standardlib import _json as json
from grimmclub_standardlib import _yaml as yaml

# json is the logging wrapper (a drop-in for the stdlib module), not stdlib json.
from grimmclub_standardlib._core import false, no, off, on, true, yes

# Path is the logging subclass of pathlib.Path (still an instance of it).
from grimmclub_standardlib._path import Path
from grimmclub_standardlib.log import banner, debug, debug_enabled, log, set_debug

__all__ = [
    # modules
    "os",
    "sys",
    "json",
    "yaml",
    "math",
    "random",
    "itertools",
    "textwrap",
    # pathlib
    "Path",
    "SystemPath",
    # dataclasses
    "dataclass",
    "field",
    # enum
    "Enum",
    "IntEnum",
    "StrEnum",
    "auto",
    # typing
    "Any",
    "Optional",
    "Protocol",
    "TYPE_CHECKING",
    "IO",
    "TextIO",
    "BinaryIO",
    # datetime
    "date",
    "datetime",
    "time",
    "timedelta",
    # collections
    "Counter",
    "defaultdict",
    "deque",
    # teaching helpers
    "log",
    "debug",
    "debug_enabled",
    "set_debug",
    "banner",
    # the house vocabulary
    "yes",
    "no",
    "true",
    "false",
    "on",
    "off",
]
