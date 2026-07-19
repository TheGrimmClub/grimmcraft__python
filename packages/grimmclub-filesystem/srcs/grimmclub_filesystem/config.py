"""Load and save the shared ``config.yaml`` that ties the tools together.

``town`` edits this file through its UI; the command-line tools (``guard`` …)
read it for their defaults. Keeping it in one place means "the data" lives in
exactly one obvious spot.
"""

# [ ] Includes external
import yaml

# [ ] Includes internal
from grimmclub_filesystem.core import (
    Any,
    SystemPath,
    SystemPathOptional,
    path_like,
    path_like_optional,
)
from grimmclub_filesystem.paths import as_path

CONFIG_NAME = "config.yaml"
BACKUP_SUFFIX = ".bak"

DEFAULT_CONFIG: dict[str, Any] = {
    "guard": {
        "world_dir": "./_input",
        "archive_dir": "./_backups",
        "restore_dir": "./_restore",
        "write_docs": True,
        "sources": {},
    },
    "scout": {},
    "blacksmith": {},
    "town": {"host": "127.0.0.1", "port": 8080},
}


def find_config(start: path_like_optional = None) -> SystemPathOptional:
    """Walk up from ``start`` (or cwd) looking for a ``config.yaml``."""
    here = as_path(start or SystemPath.cwd()).resolve()
    for folder in (here, *here.parents):
        candidate = folder / CONFIG_NAME
        if candidate.is_file():
            return candidate
    return None


def load_config(path: path_like_optional = None) -> dict[str, Any]:
    """Load the config, falling back to :data:`DEFAULT_CONFIG` when absent."""
    found = as_path(path) if path else find_config()
    if not found or not SystemPath(found).is_file():
        return dict(DEFAULT_CONFIG)
    data = yaml.safe_load(SystemPath(found).read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"{found} must contain a YAML mapping at the top level")
    return data


def backup_path(path: path_like) -> SystemPath:
    """The sibling path where :func:`save_config` keeps the previous version.

    e.g. ``config.yaml`` -> ``config.yaml.bak``.
    """
    dest = as_path(path)
    return dest.with_name(dest.name + BACKUP_SUFFIX)


def save_config(data: dict[str, Any], path: path_like) -> SystemPath:
    """Write ``data`` back to ``path`` as tidy YAML.

    Before overwriting, the current file (if any) is copied to a ``.bak``
    backup so the last version can always be restored — see
    :func:`restore_config`.
    """
    dest = as_path(path)
    if dest.is_file():
        backup_path(dest).write_bytes(dest.read_bytes())
    dest.write_text(
        yaml.safe_dump(data, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    return dest


def restore_config(path: path_like) -> SystemPathOptional:
    """Restore ``path`` from the ``.bak`` backup left by :func:`save_config`.

    Returns the restored path, or ``None`` if there is no backup yet.
    """
    dest = as_path(path)
    backup = backup_path(dest)
    if not backup.is_file():
        return None
    dest.write_bytes(backup.read_bytes())
    return dest
