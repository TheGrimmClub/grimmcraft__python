"""grimmclub — a curated facade over the Python standard library, for teaching.

Import the everyday "batteries" from **one** place, with the **same names and
APIs** as the stdlib, plus a few teaching helpers (:func:`log`, :func:`debug`,
:func:`banner`)::

    from grimmclub import Path, StrEnum, dataclass, field
    from grimmclub import json, math          # whole modules: json.dumps(...)
    from grimmclub import log, banner

Two shapes are re-exported:

* **common leaf names** used directly (``Path``, ``dataclass``, ``StrEnum``,
  ``Any``, ``datetime`` …) — because that is how they are normally imported;
* **whole modules** (``os``, ``sys``, ``json``, ``math``, ``random``,
  ``itertools``, ``textwrap``) — because their members (``json.dumps``,
  ``os.getcwd``) collide if flattened, and ``module.member`` reads clearest.

A flat facade can't expose *all* of the stdlib without name clashes; this is the
curated set students actually reach for. Add more here as needed — one edit, and
every script gets it.
"""

from __future__ import annotations

# --- whole modules (use as `json.dumps(...)`, `os.getcwd()`, …) --------------
import itertools
import json
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
from pathlib import Path
from typing import Any, Optional, Protocol

# --- teaching helpers --------------------------------------------------------
from grimmclub.log import banner, debug, debug_enabled, log, set_debug

__all__ = [
    # modules
    "os",
    "sys",
    "json",
    "math",
    "random",
    "itertools",
    "textwrap",
    # pathlib
    "Path",
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
]
