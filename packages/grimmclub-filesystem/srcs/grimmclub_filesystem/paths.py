"""Path helpers — find things and make folders without ceremony."""

# Includes internal
from grimmclub_filesystem.core import SystemPath, SystemPathOptional, path_like

# Constants
# Names that macOS / editors sprinkle around and that we never want in a backup.
JUNK_NAMES = {".DS_Store", "__MACOSX", "Thumbs.db", ".Spotlight-V100", ".Trashes"}

# Functions
def as_path(value: path_like) -> SystemPath:
    """Turn a string or Path into an expanded Path."""
    return SystemPath(value).expanduser()


def ensure_dir(path: path_like) -> SystemPath:
    """Create ``path`` (and parents) if missing, then return it."""
    p = as_path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def is_junk(path: path_like) -> bool:
    """True if any part of the path is macOS / editor clutter."""
    parts = as_path(path).parts
    name = as_path(path).name
    return name in JUNK_NAMES or any(part in JUNK_NAMES for part in parts)


def locate_directory(root: path_like, marker: str = "level.dat") -> SystemPathOptional:
    """Find a directory under ``root`` that contains ``marker``.

    Returns the folder holding ``marker``, or ``None`` if none is found. If
    ``root`` itself contains ``marker``, ``root`` is returned unchanged. The
    default marker (``level.dat``) makes this locate a Minecraft world folder.
    """
    root = as_path(root)
    if not root.exists():
        return None
    if (root / marker).is_file():
        return root
    for hit in sorted(root.rglob(marker)):
        if not is_junk(hit):
            return hit.parent
    return None
