"""filesystem — the single, learner-friendly interface to the file world.

Instead of importing ``os``, ``pathlib``, ``zipfile``, ``ftplib`` and
``urllib`` all over the place, the GrimmCraft Town tools import *this* package.
It keeps the "how do I touch files, archives and remote servers" knowledge
in one small, well-documented place.

Minecraft-specific reading (NBT, regions, world info) lives in the sibling
``grimmcraft_world`` package, which builds on this one.

Quick tour::

    from grimmclub_filesystem import paths, archive, transfer, config

    world = paths.locate_directory("./_input")   # find a folder with level.dat
    archive.create_archive(world, "out.zip")     # zip it (skips macOS junk)
"""

from grimmclub_filesystem import archive, config, core, paths, transfer
from grimmclub_filesystem.checks import (
    ContentError,
    expect_dir,
    expect_file,
    expect_json,
    expect_json_object,
)
from grimmclub_filesystem.core import SystemPath

__all__ = [
    "core",
    "checks",
    "archive",
    "config",
    "paths",
    "SystemPath",
    "ContentError",
    "expect_file",
    "expect_dir",
    "expect_json",
    "expect_json_object",
    "transfer",
]

__version__ = "2026.1.0"
