"""
Zip archives — create and restore, without the macOS ``__MACOSX`` junk.

# Classes:

- `Archive( name, path )`

# Functions:

- `create_archive(from, to, name)`: using `Archive.create()`
- `extract_archive(zip, to)`: using `Archive.extract()`
- `list_archive(zip)`: using `Archive.list()`
- `is_valid_archive(zip)`: using `Archive.exists()`

"""

# Includes internal
from posixpath import exists

from grimmclub_filesystem.core import (
    ZIP_DEFLATED,
    StringChecker,
    SystemPath,
    ZipFile,
    get_iso_date,
    no,
    path_like,
    yes,
)
from grimmclub_filesystem.paths import as_path, ensure_dir, is_junk

# Constants
FORBIDDEN_CHARACTERS = ' ' # TODO: all characters

# Main Class
#
class Archive:
    """A simple accessor class for archives.
    TODO: create tests
    """
    def __init__(self, name : str, do_cleanup : bool = yes):
        self.checker : StringChecker = StringChecker()
        if do_cleanup:
            name = self.get_valid_name(name)
        self.name : str = name

    def get_valid_name(self, name : str) -> str:
        # empty name
        if not name:
            name = 'archive'

        # now spaces (replace them with `_`)
        name = name.replace(" ", "_")

        # now special characters
        name = "".join(c for c in name if c not in self.checker.special_chars)

        # lower case
        name = name.lower()

        return name

    def is_valid_name(self, name: str | None = None, do_needs_date=no) -> bool:
        """check if this or the local name is a valid name"""
        if name == None:
          name = self.name

        result = yes # start positive

        # check forbidden characters
        for check_for in FORBIDDEN_CHARACTERS:  # TODO: all characters
            if name.count(' ') == 0:
              result = no

        # optional checks
        if do_needs_date == yes:
            pass # TODO: implement a `__{date}` check
        return result



    def exists(self) -> bool:
        return SystemPath(self.name).exists()

    def list(self, zip_path: path_like) -> list[str]:
        with ZipFile(zip_path) as zf:
            return [name for name in zf.namelist() if not is_junk(name)]

    def append_date(self, info: path_like) -> str:
        if type(info) is SystemPath:
            active : str = info.name
        else:
            active = str(info)

        active = active + f"__{get_iso_date()}"
        return active

    def create(self,
               from_path: path_like,
               to_path: path_like,
               do_date : bool = yes) -> SystemPath:
        """Zip the folder ``from_path`` into ``to_path``.
        The name is already given by ``self.name``.

        Junk files (``.DS_Store``, ``__MACOSX`` …) are skipped.
        """

        source_path = as_path(from_path)
        if not source_path.is_dir():
            raise NotADirectoryError(f"Cannot archive, not a folder: {source_path}")

        filter_name =  source_path.name

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

        return full_path


    def extract(self,
                zip_path: path_like,
                to_path: path_like,
                do_overwrite: bool = no) -> SystemPath:
        """Extract ``zip_path`` into ``to_path`` (created if needed).
        - `do_overwrite`: if `yes`, existing files will be overwritten.
        Junk entries are skipped. Returns the destination folder.
        """
        source_path = as_path(zip_path)
        if not source_path.is_file():
            raise FileNotFoundError(f"Archive not found: {source_path}")

        destination_path = ensure_dir(to_path)
        with ZipFile(source_path) as zf:
            for member in zf.namelist():
                if is_junk(member):
                    continue
                _ = zf.extract(member, to_path)


        return destination_path

# Function interface

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
    # The Archive *name* is only a label here, so derive it from the file name —
    # but always open the archive through the full path, or a zip outside the
    # working directory would not be found.
    archive = Archive(as_path(zip_path).name)
    return archive.extract(zip_path, to_path)


def list_archive(zip_path: path_like) -> list[str]:
    """Return the (non-junk) entry names inside ``zip_path``."""
    archive = Archive(as_path(zip_path).name)
    return archive.list(zip_path)

def is_valid_archive(zip_path: path_like, do_name_validation=yes) -> bool
    """Check an archvie for existance and other things."""
    if type(zip_path) == str:
        zip_path = as_path(zip_path)

    archive = Archive(zip_path.name)
    result = zip_path.exists()
    if do_name_validation == yes:
        result &= archive.is_valid_name()
