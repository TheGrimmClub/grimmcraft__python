"""Load and save a shared ``config.yaml``.

One file, one obvious place, and a ``.bak`` of the previous version whenever it
is written — so an edit that goes wrong is always one `restore()` from undone.

# Classes:

- `Config( path, defaults )`

# Functions:

- `register_defaults(section, defaults)`: what a tool contributes to a fresh file
- `default_config()`: every registered section, merged
- `find_config(start)`: walk up looking for a `config.yaml`
- `load_config(path)`: using `Config.load()`
- `save_config(data, path)`: using `Config.save()`
- `backup_path(path)`: where `save` keeps the previous version
- `restore_config(path)`: using `Config.restore()`

The class is the interface; the functions are thin wrappers, kept for callers
that want one operation and no object.

**This module ships no application defaults.** It cannot know which sections a
tool wants, and hard-coding one project's layout is what made the previous
version specific to a repository this package no longer lives in. Each tool
registers its own::

    register_defaults("guard", {"world_dir": "./_input", "sources": {}})
"""

# Includes external
# Includes internal
from grimmclub_filesystem.core import (
    Any,
    SystemPath,
    SystemPathOptional,
    no,
    path_like,
    path_like_optional,
    yes,
)
from grimmclub_filesystem.paths import as_path
from grimmclub_standardlib import yaml

# Constants

#: The file name searched for when walking up the tree.
CONFIG_NAME = "config.yaml"

#: Appended to make the backup written before every overwrite.
BACKUP_SUFFIX = ".bak"

#: Section -> defaults, contributed by applications via `register_defaults`.
#: Deliberately empty here: a filesystem library has no opinion about what a
#: configuration should contain.
_REGISTERED_DEFAULTS: dict[str, dict[str, Any]] = {}


def register_defaults(section: str, defaults: dict[str, Any]) -> None:
    """Declare the defaults for one ``section`` of the configuration.

    Called once at import time by each tool that reads the shared file::

        register_defaults("guard", {"world_dir": "./_input"})

    Registering the same section twice replaces it, so a test can install its
    own without leaking into the next one — see :func:`unregister_defaults`.
    """
    _REGISTERED_DEFAULTS[section] = dict(defaults)


def unregister_defaults(section: str) -> None:
    """Forget a section's defaults; does nothing if it has none."""
    _REGISTERED_DEFAULTS.pop(section, None)


def default_config() -> dict[str, Any]:
    """Every registered section, as a fresh dictionary.

    A copy, so a caller mutating the result cannot change what the next call
    returns. The previous module-level constant could be edited in place by
    accident, which is a poor property for a default.
    """
    return {section: dict(values) for section, values in _REGISTERED_DEFAULTS.items()}


# Classes

class Config:
    """A configuration file: where it is, what it holds, and how to write it.

    Reading is lazy — nothing touches the disk until :attr:`data` is used — and
    the file is written only when asked::

        config = Config("config.yaml")
        config["town"]["port"] = 9090
        config.save()

    As a context manager it saves on the way out, and *only* on a clean exit::

        with Config("config.yaml") as config:
            config["town"]["port"] = 9090
        # saved here, previous version kept as config.yaml.bak

    That is where a ``with`` block earns its place: a real acquire (load) and
    release (save), and something meaningful to do when the body raises — leave
    the file alone. An edit that crashed half-way through should not be written.
    """

    def __init__(
        self,
        path: path_like_optional = None,
        *,
        defaults: dict[str, Any] | None = None,
    ) -> None:
        self._path: SystemPath | None = None
        self.path = path if path is not None else find_config()
        self._defaults = default_config() if defaults is None else dict(defaults)
        self._data: dict[str, Any] | None = None
        self._loaded_from_disk = no

    # --- path ----------------------------------------------------------------
    @property
    def path(self) -> SystemPath | None:
        """Where the configuration is read from and written to."""
        return self._path

    @path.setter
    def path(self, value: path_like_optional) -> None:
        self._path = None if value is None else as_path(value)
        # A new path means anything already loaded no longer describes it.
        self._data = None

    @property
    def backup_path(self) -> SystemPath:
        """Where :meth:`save` keeps the previous version (``config.yaml.bak``)."""
        if self._path is None:
            raise ValueError("this Config has no path, so it has no backup path")
        return self._path.with_name(self._path.name + BACKUP_SUFFIX)

    @property
    def exists(self) -> bool:
        """Whether the file is on disk yet."""
        return self._path is not None and self._path.is_file()

    @property
    def loaded_from_disk(self) -> bool:
        """True when :attr:`data` came from a file rather than from defaults."""
        _ = self.data  # force the lazy load, so the answer means something
        return self._loaded_from_disk

    # --- data ----------------------------------------------------------------
    @property
    def data(self) -> dict[str, Any]:
        """The configuration, loaded on first use."""
        if self._data is None:
            self._data = self.load()
        return self._data

    @data.setter
    def data(self, value: dict[str, Any]) -> None:
        self._data = dict(value)

    def load(self) -> dict[str, Any]:
        """Read the file, falling back to the registered defaults when absent."""
        if self._path is None or not self._path.is_file():
            self._loaded_from_disk = no
            self._data = self._defaults_copy()
            return self._data

        document = yaml.loads(self._path.read_text(encoding="utf-8")) or {}
        if not isinstance(document, dict):
            raise ValueError(
                f"{self._path} must contain a YAML mapping at the top level, "
                f"but holds a {type(document).__name__}"
            )
        self._loaded_from_disk = yes
        self._data = document
        return self._data

    def save(self, path: path_like_optional = None) -> SystemPath:
        """Write the configuration, keeping the previous version as ``.bak``."""
        if path is not None:
            self.path = as_path(path)
        if self._path is None:
            raise ValueError("this Config has no path to save to")

        destination = self._path
        if destination.is_file():
            self.backup_path.write_bytes(destination.read_bytes())
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(
            yaml.dumps(self.data, allow_unicode=True),
            encoding="utf-8",
        )
        return destination

    def restore(self) -> SystemPathOptional:
        """Put the ``.bak`` back, or return ``None`` if there is no backup."""
        if self._path is None or not self.backup_path.is_file():
            return None
        self._path.write_bytes(self.backup_path.read_bytes())
        self._data = None  # what is held no longer matches the file
        return self._path

    # --- reading and writing sections ----------------------------------------
    def section(self, name: str) -> dict[str, Any]:
        """One section, created empty if the file does not have it yet."""
        existing = self.data.setdefault(name, {})
        return existing if isinstance(existing, dict) else {}

    def get(self, section: str, key: str, default: Any = None) -> Any:
        """One value, without worrying whether its section exists."""
        found = self.data.get(section)
        return found.get(key, default) if isinstance(found, dict) else default

    def set(self, section: str, key: str, value: Any) -> None:
        """Set one value, creating the section if needed."""
        self.section(section)[key] = value

    def __getitem__(self, section: str) -> Any:
        return self.data[section]

    def __setitem__(self, section: str, value: Any) -> None:
        self.data[section] = value

    def __contains__(self, section: object) -> bool:
        return section in self.data

    def _defaults_copy(self) -> dict[str, Any]:
        return {section: dict(values) for section, values in self._defaults.items()}

    # --- context manager -----------------------------------------------------
    def __enter__(self) -> "Config":
        _ = self.data  # load now, so a failure surfaces at the `with`, not later
        return self

    def __exit__(self, exception_type: object, *_rest: object) -> None:
        # Save only on a clean exit: a body that raised may have left the
        # configuration half-edited, and writing that is worse than losing it.
        #
        # Returns None rather than False on purpose: a `bool` return type tells
        # type checkers this *might* suppress the exception, and it never does.
        if exception_type is None and self._path is not None:
            self.save()

    def __repr__(self) -> str:
        return f"Config(path={self._path!r}, sections={sorted(self.data)})"


# Functions

def find_config(start: path_like_optional = None) -> SystemPathOptional:
    """Walk up from ``start`` (or cwd) looking for a ``config.yaml``."""
    here = as_path(start or SystemPath.cwd()).resolve()
    for folder in (here, *here.parents):
        candidate = folder / CONFIG_NAME
        if candidate.is_file():
            return candidate
    return None


def load_config(path: path_like_optional = None) -> dict[str, Any]:
    """Load the config, falling back to the registered defaults when absent."""
    return Config(path if path is not None else find_config()).load()


def backup_path(path: path_like) -> SystemPath:
    """The sibling path where :func:`save_config` keeps the previous version.

    e.g. ``config.yaml`` -> ``config.yaml.bak``.
    """
    destination = as_path(path)
    return destination.with_name(destination.name + BACKUP_SUFFIX)


def save_config(data: dict[str, Any], path: path_like) -> SystemPath:
    """Write ``data`` to ``path`` as tidy YAML, keeping a ``.bak`` of the old."""
    config = Config(path)
    config.data = data
    return config.save()


def restore_config(path: path_like) -> SystemPathOptional:
    """Restore ``path`` from the ``.bak`` left by :func:`save_config`.

    Returns the restored path, or ``None`` if there is no backup yet.
    """
    return Config(path).restore()
