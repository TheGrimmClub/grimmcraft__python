"""Path helpers — find things and make folders without ceremony.

# Classes:
-

# Functions:
- `as_path(str|path_like)`
- `create_full_path(path_like)`
- `is_junk_directory(path_like)`
- `locate_directory(path_like)`
"""

# Includes standard
from fnmatch import fnmatch

# Includes internal
from grimmclub_filesystem.core import SystemPath, SystemPathOptional, path_like

# Constants

#: Exact names an operating system or editor leaves behind, and what each is.
#:
#: Keeping the *reason* beside the name is what lets `junk_reason()` explain a
#: skipped file, and stops the table becoming a list of magic strings nobody
#: dares remove.
JUNK_NAMES: dict[str, str] = {
    # --- macOS ---------------------------------------------------------------
    ".DS_Store": "macOS Finder folder settings",
    "__MACOSX": "macOS resource-fork folder added when zipping",
    ".Spotlight-V100": "macOS Spotlight index",
    ".Trashes": "macOS per-volume trash",
    ".fseventsd": "macOS filesystem event log",
    ".TemporaryItems": "macOS temporary items",
    ".DocumentRevisions-V100": "macOS document version store",
    ".apdisk": "macOS Time Machine disk marker",
    ".AppleDouble": "macOS resource-fork sidecar folder",
    ".VolumeIcon.icns": "macOS custom volume icon",
    # --- Windows -------------------------------------------------------------
    "Thumbs.db": "Windows Explorer thumbnail cache",
    "ehthumbs.db": "Windows Media Center thumbnail cache",
    "Desktop.ini": "Windows Explorer folder settings",
    "$RECYCLE.BIN": "Windows recycle bin",
    "System Volume Information": "Windows restore-point store",
    # --- Linux ---------------------------------------------------------------
    ".directory": "KDE folder settings",
    ".Trash": "Linux trash folder",
    # --- editors and tools ---------------------------------------------------
    ".idea": "JetBrains project settings",
    ".vscode": "VS Code workspace settings",
}

#: Patterns for junk whose name varies, so an exact set cannot catch it.
#: Matched against the file name only, case-insensitively on the platforms that
#: are case-insensitive anyway.
JUNK_PATTERNS: dict[str, str] = {
    "._*": "macOS AppleDouble resource fork",
    ".Trash-*": "Linux per-user trash folder",
    ".nfs*": "NFS silly-rename placeholder for a still-open deleted file",
    "~$*": "Microsoft Office lock file",
    "*.icloud": "iCloud placeholder for a file that has not been downloaded",
    "*.swp": "Vim swap file",
    "*.swo": "Vim swap file",
    "*~": "editor backup copy",
}

# Functions
def as_path(value: path_like) -> SystemPath:
    """Turn a string or Path into an expanded Path."""
    return SystemPath(value).expanduser()


def create_full_path(path: path_like) -> SystemPath:
    """Create ``path`` (and parents) if missing, then return it."""
    p = as_path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def junk_reason(path: path_like) -> str | None:
    """Why ``path`` counts as junk, or ``None`` if it does not.

    Checks **every component**, not just the file name: anything inside a
    `__MACOSX` or `$RECYCLE.BIN` folder is junk by virtue of where it sits, even
    when its own name looks ordinary.

    Returning the reason rather than a bare boolean means a tool can say *why*
    it skipped a file, which is the difference between "3 files skipped" and
    "3 files skipped: macOS Finder folder settings".
    """
    # Deliberately NOT `as_path`: that expands `~`, and a file genuinely named
    # `~$report.docx` (an Office lock file) is exactly what we are looking for.
    # Nothing here needs the path resolved — only its components read.
    for component in SystemPath(path).parts:
        reason = JUNK_NAMES.get(component)
        if reason is not None:
            return reason
        for pattern, description in JUNK_PATTERNS.items():
            if fnmatch(component, pattern):
                return description
    return None


def is_junk_path(path: path_like) -> bool:
    """True if any part of ``path`` is operating-system or editor clutter.

    Covers macOS, Windows and Linux, plus the editors and sync tools that
    litter a working tree — see :data:`JUNK_NAMES` and :data:`JUNK_PATTERNS`.
    """
    return junk_reason(path) is not None


#: Kept because callers already use this name. It is a slight misnomer — the
#: check applies to files as much as folders (`.DS_Store` and `Thumbs.db` are
#: files), and it is called on zip members — so `is_junk_path` is the accurate
#: spelling and this is an alias.
is_junk_directory = is_junk_path


def locate_directory(root: path_like, marker: str) -> SystemPathOptional:
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
        if not is_junk_directory(hit):
            return hit.parent
    return None
