"""
Zip archives — create and restore, without the macOS ``__MACOSX`` junk.

# Classes:

- `Archive( name, path )`

# Functions:

- `create_archive(from, to, name)`: using `Archive.create()`
- `extract_archive(zip, to)`: using `Archive.extract()`
- `list_archive(zip)`: using `Archive.list()`
- `is_valid_archive(zip)`: using `Archive.exists()` and `Archive.is_valid_name()`

An `Archive` knows two things: its **name** and the **folder it lives in**.
Both are properties, so assigning to either keeps the object consistent — a name
is always cleaned, a path is always a `SystemPath` — and `full_path` is derived
from them rather than stored, so the three can never disagree.
"""

# [ ] Includes internal
from grimmclub_filesystem.core import (
    ZIP_DEFLATED,
    BadZipFile,
    StringChecker,
    SystemPath,
    ZipFile,
    get_iso_date,
    no,
    path_like,
    path_like_optional,
    yes,
)
from grimmclub_filesystem.paths import as_path, ensure_dir, is_junk

# [ ] Constants

#: Characters no archive name may contain.
#:
#: The union of what Windows forbids outright (``< > : " / \ | ? *`` plus the
#: control characters) and the path separators POSIX forbids. A name that avoids
#: all of these is safe to write on any platform we might restore onto, which is
#: the point — an archive is a thing you hand to someone else.
FORBIDDEN_CHARACTERS: frozenset[str] = frozenset(
    '<>:"/\\|?*' + "".join(chr(code) for code in range(32))
)

#: Names Windows reserves whatever the extension, and so cannot be used at all.
RESERVED_NAMES: frozenset[str] = frozenset(
    ["con", "prn", "aux", "nul"]
    + [f"com{digit}" for digit in range(1, 10)]
    + [f"lpt{digit}" for digit in range(1, 10)]
)

#: What an archive is called when no usable name was given.
DEFAULT_ARCHIVE_NAME = "archive"

#: Separator between an archive's stem and its date stamp.
DATE_SEPARATOR = "__"


# [ ] Main Class
#
class Archive:
    """A zip archive: a cleaned ``name``, the ``path`` it lives in, and the
    operations you can perform on it.

    ``path`` is optional — omit it and the archive is simply "a name", which is
    all `create_archive` needs, since `create()` is told where to write. Give it
    one and `exists()`, `list()` and `extract()` can work without being handed a
    path every time.
    """

    def __init__(
        self,
        name: str,
        path: path_like_optional = None,
        do_cleanup: bool = yes,
    ) -> None:
        self.checker: StringChecker = StringChecker()
        self._do_cleanup: bool = do_cleanup
        # Assign through the properties so construction and later assignment
        # apply exactly the same rules.
        self.name = name
        self.path = path

    # --- name ----------------------------------------------------------------
    @property
    def name(self) -> str:
        """The archive's file name, cleaned unless ``do_cleanup`` was disabled."""
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        self._name = self.get_valid_name(value) if self._do_cleanup else value

    # --- path ----------------------------------------------------------------
    @property
    def path(self) -> SystemPath | None:
        """The folder the archive lives in, or ``None`` if it has no home yet."""
        return self._path

    @path.setter
    def path(self, value: path_like_optional) -> None:
        # Coerce here so every reader gets a SystemPath and callers may pass a
        # plain string, which is the whole reason this is a property.
        self._path = None if value is None else as_path(value)

    @property
    def full_path(self) -> SystemPath:
        """Where the archive is (or would be) on disk: ``path / name``.

        Derived rather than stored, so it cannot drift out of step with the two
        values it is built from. With no ``path`` set this is just the name,
        which resolves relative to the working directory.
        """
        return SystemPath(self.name) if self._path is None else self._path / self.name

    # --- names ---------------------------------------------------------------
    def get_valid_name(self, name: str) -> str:
        """Clean ``name`` into something safe to write on any platform."""
        # empty name
        if not name:
            name = DEFAULT_ARCHIVE_NAME

        # now spaces (replace them with `_`)
        name = name.replace(" ", "_")

        # now special characters
        name = "".join(c for c in name if c not in self.checker.special_chars)

        # lower case
        name = name.lower()

        # cleaning can empty a name that was nothing but punctuation
        if not name or name in RESERVED_NAMES:
            name = DEFAULT_ARCHIVE_NAME

        return name

    def is_valid_name(self, name: str | None = None, do_needs_date: bool = no) -> bool:
        """Whether ``name`` (or this archive's own name) is usable.

        A name is valid when it is non-empty, contains no forbidden character,
        and is not one of the names Windows reserves. With ``do_needs_date`` it
        must also carry a ``__YYYYMMDD`` stamp, which is how `create()` labels
        dated backups.
        """
        if name is None:
            name = self.name

        if not name:
            return no

        # check forbidden characters
        for character in name:
            if character in FORBIDDEN_CHARACTERS:
                return no

        # a reserved name is refused whatever its extension
        if SystemPath(name).stem.lower() in RESERVED_NAMES:
            return no

        # optional checks
        if do_needs_date == yes:
            return self.has_date(name)

        return yes

    @staticmethod
    def has_date(name: str) -> bool:
        """Whether ``name`` carries a ``__YYYYMMDD`` stamp from :meth:`append_date`."""
        stem = SystemPath(name).stem
        _, separator, tail = stem.rpartition(DATE_SEPARATOR)
        return bool(separator) and len(tail) == 8 and tail.isdigit()

    def append_date(self, info: path_like) -> str:
        """Add today's date to ``info``, before any extension.

        ``backup.zip`` becomes ``backup__20260719.zip`` rather than
        ``backup.zip__20260719`` — the suffix has to stay last, or the file is no
        longer recognisably a zip.
        """
        if type(info) is SystemPath:
            active: str = info.name
        else:
            active = str(info)

        path = SystemPath(active)
        return f"{path.stem}{DATE_SEPARATOR}{get_iso_date()}{path.suffix}"

    # --- the archive itself --------------------------------------------------
    def exists(self) -> bool:
        """Whether the archive exists on disk at :attr:`full_path`."""
        return self.full_path.is_file()

    def list(self, zip_path: path_like_optional = None) -> list[str]:
        """The (non-junk) entry names inside the archive."""
        target = self.full_path if zip_path is None else as_path(zip_path)
        with ZipFile(target) as zf:
            return [name for name in zf.namelist() if not is_junk(name)]

    def create(
        self,
        from_path: path_like,
        to_path: path_like,
        do_date: bool = yes,
    ) -> SystemPath:
        """Zip the folder ``from_path`` into ``to_path``.
        The name is already given by ``self.name``.

        Junk files (``.DS_Store``, ``__MACOSX`` …) are skipped. The archive's
        :attr:`path` is set to ``to_path``, so the object afterwards describes
        the file it just wrote.
        """

        source_path = as_path(from_path)
        if not source_path.is_dir():
            raise NotADirectoryError(f"Cannot archive, not a folder: {source_path}")

        filter_name = source_path.name

        destination_path = as_path(to_path)
        _ = ensure_dir(destination_path)

        archive_name = self.append_date(self.name) if do_date else self.name
        full_path = destination_path / archive_name
        with ZipFile(full_path, "w", ZIP_DEFLATED) as zf:
            for item in sorted(source_path.rglob("*")):
                if is_junk(item):
                    continue
                rel = SystemPath(filter_name) / item.relative_to(source_path)
                if item.is_dir():
                    # store an explicit directory entry so empty folders survive
                    zf.writestr(str(rel) + "/", "")
                else:
                    zf.write(item, str(rel))

        # The object now describes a real file; remember where it went.
        self.path = destination_path
        return full_path

    def extract(
        self,
        zip_path: path_like_optional = None,
        to_path: path_like = ".",
        do_overwrite: bool = no,
    ) -> SystemPath:
        """Extract the archive into ``to_path`` (created if needed).

        - ``zip_path``: which archive; defaults to this one's :attr:`full_path`.
        - ``do_overwrite``: if ``no`` (the default), entries that already exist
          on disk are left alone rather than replaced.

        Junk entries are skipped. Returns the destination folder.
        """
        source_path = self.full_path if zip_path is None else as_path(zip_path)
        if not source_path.is_file():
            raise FileNotFoundError(f"Archive not found: {source_path}")

        destination_path = ensure_dir(to_path)
        with ZipFile(source_path) as zf:
            for member in zf.namelist():
                if is_junk(member):
                    continue
                if do_overwrite == no and (destination_path / member).exists():
                    continue
                _ = zf.extract(member, destination_path)

        return destination_path

    def __repr__(self) -> str:
        return f"Archive(name={self.name!r}, path={self.path!r})"


# [ ] Function interface

def create_archive(
    from_path: path_like,
    to_path: path_like,
    *,
    archive_name: str
) -> SystemPath:
    """Zip the folder ``from_path`` into ``to_path``.

    ``archive_name`` is the fist_folder-level folder name stored *inside* the zip. For a
    Minecraft backup we want ``"world"`` so the archive always restores to a
    tidy ``world/`` folder, regardless of what the source_path folder was called.
    Junk files (``.DS_Store``, ``__MACOSX`` …) are skipped.
    """
    archive = Archive(archive_name)
    result_path = archive.create(from_path, to_path)
    return result_path


def extract_archive(zip_path: path_like, to_path: path_like) -> SystemPath:
    """Extract ``zip_path`` into ``to_path`` (created if needed).

    Junk entries are skipped. Returns the destination folder.
    """
    # The name is only a label; the archive is opened through its full path, so
    # a zip outside the working directory is still found.
    source = as_path(zip_path)
    archive = Archive(source.name, source.parent, do_cleanup=no)
    return archive.extract(to_path=to_path)


def list_archive(zip_path: path_like) -> list[str]:
    """Return the (non-junk) entry names inside ``zip_path``."""
    source = as_path(zip_path)
    archive = Archive(source.name, source.parent, do_cleanup=no)
    return archive.list()


def is_valid_archive(zip_path: path_like, do_name_validation: bool = yes) -> bool:
    """Whether ``zip_path`` is an archive we can use.

    Checks that the file exists, that it really is a readable zip, and — unless
    ``do_name_validation`` is turned off — that its name is safe to restore onto
    any platform. Existence alone is not enough: a truncated download exists.
    """
    source = as_path(zip_path)
    archive = Archive(source.name, source.parent, do_cleanup=no)

    if not archive.exists():
        return no

    if do_name_validation == yes and not archive.is_valid_name():
        return no

    # A file that is not a readable zip is not a usable archive, however good
    # its name looks.
    try:
        with ZipFile(source) as zf:
            # testzip() reads every entry's CRC, so a truncated or corrupted
            # archive is caught here rather than at restore time.
            return zf.testzip() is None
    except (BadZipFile, OSError, ValueError):
        return no
