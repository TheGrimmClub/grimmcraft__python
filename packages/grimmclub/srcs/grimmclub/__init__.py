"""grimmclub — the single access point for teachers and trainees.

Import everything from **one** place::

    from grimmclub import Path, dataclass, StrEnum   # the standard library
    from grimmclub import log, banner, yes, no       # teaching helpers
    from grimmclub import archive, paths, expect     # working with files

There is nothing else to learn about where things live: if the club provides it,
``from grimmclub import …`` has it.

# Layers

This package is the **front door**, and deliberately holds no implementation of
its own — it re-exports the libraries beneath it:

- :mod:`grimmclub_standardlib` — a facade over the standard library (``os``,
  ``sys``, ``pathlib`` …) plus the logging helpers and the house vocabulary
  (``yes``/``no``). It has no dependencies, so anything may rely on it.
- :mod:`grimmclub_filesystem` — the one interface to the file world: paths,
  archives, transfers, configuration, and the ``expect_*`` guards.

Further libraries join the same way: add the dependency, re-export it here.

The split exists so that a *working* library can share the house vocabulary
without depending on the teaching front door. ``grimmcraft-decompiler`` needs
``expect_file`` and archive handling; it should not thereby acquire a curated
re-export of ``itertools``. Trainees are spared the distinction — they import
``grimmclub`` and get the lot.

# A note on ``Path``

``grimmclub.Path`` is the *logging* subclass from the standard-library facade:
it debug-logs the reads and writes it performs, so a lesson can show what a
program actually touches. ``grimmclub_filesystem`` deliberately uses plain
``pathlib.Path`` instead (as ``SystemPath``) — a backup tool that logged every
file it copied would be unusable. Both are ``pathlib.Path`` instances, so they
mix freely.
"""

from __future__ import annotations

# --- the file world ----------------------------------------------------------
from grimmclub_filesystem import archive, checks, config, core, paths, transfer
from grimmclub_filesystem.archive import Archive
from grimmclub_filesystem.checks import (
    ContentError,
    FileType,
    expect,
    expect_archive,
    expect_binary,
    expect_directory,
    expect_executable,
    expect_file,
    expect_json,
    expect_json_object,
    expect_link,
    expect_markdown,
    expect_script,
    expect_text,
    expect_yaml,
    expect_yaml_document,
    expect_yaml_mapping,
)
from grimmclub_filesystem.config import Config
from grimmclub_filesystem.core import SystemPath

# --- the standard library, the teaching helpers, the house vocabulary --------
from grimmclub_standardlib import (
    Any,
    Counter,
    Enum,
    IntEnum,
    Optional,
    Path,
    Protocol,
    StrEnum,
    auto,
    banner,
    dataclass,
    date,
    datetime,
    debug,
    debug_enabled,
    defaultdict,
    deque,
    false,
    field,
    itertools,
    json,
    log,
    math,
    no,
    off,
    on,
    os,
    random,
    set_debug,
    sys,
    textwrap,
    time,
    timedelta,
    true,
    yaml,
    yes,
)

__all__ = [
    # --- standard library: whole modules
    "os",
    "sys",
    "json",
    "yaml",
    "math",
    "random",
    "itertools",
    "textwrap",
    # --- standard library: leaf names
    "Path",
    "dataclass",
    "field",
    "Enum",
    "IntEnum",
    "StrEnum",
    "auto",
    "Any",
    "Optional",
    "Protocol",
    "date",
    "datetime",
    "time",
    "timedelta",
    "Counter",
    "defaultdict",
    "deque",
    # --- teaching helpers
    "log",
    "debug",
    "debug_enabled",
    "set_debug",
    "banner",
    # --- the house vocabulary
    "yes",
    "no",
    "true",
    "false",
    "on",
    "off",
    # --- the file world: whole modules
    "archive",
    "checks",
    "config",
    "core",
    "paths",
    "transfer",
    # --- the file world: leaf names
    "Archive",
    "Config",
    "SystemPath",
    "ContentError",
    "FileType",
    "expect",
    "expect_archive",
    "expect_binary",
    "expect_directory",
    "expect_executable",
    "expect_file",
    "expect_json",
    "expect_json_object",
    "expect_link",
    "expect_markdown",
    "expect_script",
    "expect_text",
    "expect_yaml",
    "expect_yaml_document",
    "expect_yaml_mapping",
]
