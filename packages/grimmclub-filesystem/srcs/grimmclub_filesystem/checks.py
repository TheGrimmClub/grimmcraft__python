"""Guards that fail *usefully* — ``expect_file``, ``expect_directory``, ``expect_json``.

A bare ``path.exists()`` tells you something is wrong but not what, and the four
ways a path can disappoint you mean four different things:

* the parent folder is missing — you are pointing at the wrong place entirely;
* the folder is there but the file is not — usually a typo, so we say what *is*
  there and suggest the closest name;
* it exists but is a directory (or vice versa);
* it exists but is empty — written, but nothing came out.

The same reasoning applies to *content*: a datapack that fails to load because a
JSON file has a stray comma should say which file, which line, and show it.
These raise rather than collect diagnostics, because they guard programmer
mistakes at the edges; the compiler's own :mod:`verify` stays diagnostic-shaped
for problems a *user's* pack can have.

# Classes:

- `ContentError()`

# Functions:

- `expect(file_type, path)` — dispatches on a `FileType`

Layer one (structural — what the filesystem itself can answer):

- `expect_directory()`
- `expect_file()`
- `expect_link()`

Layer two (content — text):

- `expect_text()`
- `expect_markdown()`
- `expect_script()`

Layer two (content — binary):

- `expect_binary()`
- `expect_archive()`
- `expect_executable()`

Layer three (structured documents):

- `expect_json()`
- `expect_json_object()`
- `expect_yaml_document()`
- `expect_yaml_mapping()`

Every guard raises and returns the path, so they compose. For a plain
predicate use `FileType.ARCHIVE.matches(path)`, which is where the actual
test lives — the guards only add the error message.

"""

# Includes external
# Includes standard
import difflib
import json
import os
from enum import Enum
from typing import Any

# Includes internal
from grimmclub_filesystem.core import SystemPath, is_zipfile, path_like
from grimmclub_filesystem.paths import as_path
from grimmclub_standardlib import yaml


# Types
class FileType(Enum):
    """What a path is expected to *be*, beyond merely existing.

    The values are grouped: ``1-99`` structural (what the filesystem says),
    ``100-199`` text, ``200+`` binary. That ordering is the useful part —
    :meth:`is_text` and :meth:`is_binary` read the band rather than listing
    members, so adding a kind does not mean editing three other places.

    How a kind is checked depends on how much can honestly be known. ARCHIVE
    reads the file's magic number; TEXT tries to decode it; MARKDOWN and SCRIPT
    can only go on the suffix, because nothing else distinguishes them.
    """

    DIRECTORY = 1
    FILE = 2
    LINK = 3
    TEXT = 100
    MARKDOWN = 101
    YAML = 102
    SCRIPT = 150
    BINARY = 200
    ARCHIVE = 211
    EXECUTABLE = 221

    @property
    def is_structural(self) -> bool:
        """True for kinds the filesystem itself can answer."""
        return self.value < 100

    @property
    def is_text(self) -> bool:
        return 100 <= self.value < 200

    @property
    def is_binary(self) -> bool:
        return self.value >= 200

    @property
    def suffixes(self) -> frozenset[str]:
        """Extensions conventionally used for this kind, lower-cased."""
        return _FILE_TYPE_SUFFIXES.get(self, frozenset())

    def describe(self) -> str:
        """The kind as it should read in an error message."""
        return self.name.lower()

    def matches(self, path: SystemPath) -> bool:
        """Whether ``path`` really is this kind of thing.

        Answers by inspection where that is possible and by suffix only where it
        is not — a ``.md`` file is Markdown because it is called that, but an
        archive is an archive because its bytes say so.
        """
        if self is FileType.DIRECTORY:
            return path.is_dir()
        if self is FileType.LINK:
            return path.is_symlink()
        if self is FileType.FILE:
            return path.is_file()
        if self is FileType.EXECUTABLE:
            return path.is_file() and os.access(path, os.X_OK)
        if self is FileType.ARCHIVE:
            # Magic number, not the name: a .zip that is not a zip is the whole
            # reason this check exists.
            return path.is_file() and is_zipfile(path)
        if self is FileType.BINARY:
            return path.is_file() and not _is_decodable_text(path)
        if self is FileType.TEXT:
            return path.is_file() and _is_decodable_text(path)
        # MARKDOWN and SCRIPT: nothing but the suffix distinguishes them.
        return path.is_file() and path.suffix.lower() in self.suffixes


#: Conventional extensions per kind, for the types only a name can identify.
_FILE_TYPE_SUFFIXES: dict[FileType, frozenset[str]] = {
    FileType.YAML: frozenset({".yaml", ".yml"}),
    FileType.MARKDOWN: frozenset({".md", ".markdown", ".mdown"}),
    FileType.SCRIPT: frozenset({".py", ".sh", ".bash", ".zsh", ".fish"}),
    FileType.ARCHIVE: frozenset({".zip", ".jar", ".mcpack", ".mcworld"}),
    FileType.TEXT: frozenset({".txt", ".md", ".json", ".yaml", ".yml", ".toml"}),
}

#: How much of a file to read when guessing whether it is text.
_TEXT_SNIFF_BYTES = 8192


def _is_decodable_text(path: SystemPath) -> bool:
    """Whether the start of ``path`` decodes as UTF-8 and holds no NUL byte.

    The NUL check matters because plenty of binary formats decode as UTF-8 by
    accident; no real text file contains one.
    """
    try:
        chunk = path.read_bytes()[:_TEXT_SNIFF_BYTES]
    except OSError:
        return False
    if b"\x00" in chunk:
        return False
    try:
        chunk.decode("utf-8")
    except UnicodeDecodeError:
        return False
    return True

# Constants
#: How many sibling names to list before truncating.
_MAX_SIBLINGS = 8


class ContentError(ValueError):
    """A file exists but does not hold what was expected (bad JSON, bad NBT)."""


def _siblings(path: SystemPath) -> list[str]:
    """The names of files sitting next to ``path``, sorted."""
    parent = path.parent
    if not parent.is_dir():
        return []
    return sorted(entry.name for entry in parent.iterdir() if not entry.name.startswith("."))


def _did_you_mean(path: SystemPath) -> str:
    """A ' did you mean …' clause when a sibling name is close to ``path``'s."""
    names = _siblings(path)
    if not names:
        return ""
    close = difflib.get_close_matches(path.name, names, n=1, cutoff=0.6)
    listing = ", ".join(names[:_MAX_SIBLINGS])
    if len(names) > _MAX_SIBLINGS:
        listing += f", … ({len(names)} total)"
    hint = f"\n  the folder holds: {listing}"
    if close:
        hint += f"\n  did you mean '{close[0]}'?"
    return hint


# Functions: Layer one — directories, files and links


def expect_file(
    path: path_like,
    *,
    what: str = "file",
    allow_empty: bool = True,
    file_type: FileType | None = None,
) -> SystemPath:
    """Return ``path`` as a :class:`SystemPath`, or raise explaining why not.

    ``what`` names the thing for the message ("structure file", "preset").  With
    ``allow_empty=False`` a zero-byte file is rejected too — it usually means a
    write failed halfway rather than that the file is genuinely absent.

    ``file_type`` demands the file actually *be* that kind, not merely exist
    under a promising name::

        expect_file(pack, what="datapack", file_type=FileType.ARCHIVE)

    which rejects a truncated download called ``pack.zip`` — the case where
    existence is the least useful thing to know.
    """
    target = as_path(path)
    if target.is_file():
        if not allow_empty and target.stat().st_size == 0:
            raise ContentError(f"{what} is empty: {target}")
        if file_type is not None and not file_type.matches(target):
            raise ContentError(
                f"{what} is not a valid {file_type.describe()}: {target}"
                + (
                    f"\n  expected one of: {', '.join(sorted(file_type.suffixes))}"
                    if file_type.suffixes and not file_type.is_structural
                    else ""
                )
            )
        return target

    if target.is_dir():
        raise IsADirectoryError(f"expected a {what} but found a directory: {target}")
    if not target.parent.exists():
        raise FileNotFoundError(
            f"no {what} at {target}\n  the folder {target.parent} does not exist"
        )
    raise FileNotFoundError(f"no {what} at {target}{_did_you_mean(target)}")


def expect_directory(path: path_like, *, what: str = "directory") -> SystemPath:
    """Return ``path`` as a :class:`SystemPath` directory, or raise."""
    target = as_path(path)
    if target.is_dir():
        return target
    if target.is_file():
        raise NotADirectoryError(f"expected a {what} but found a file: {target}")
    raise FileNotFoundError(f"no {what} at {target}{_did_you_mean(target)}")


def expect_link(path: path_like, *, what: str = "symbolic link") -> SystemPath:
    """Require ``path`` to be a symbolic link.

    Checked with ``is_symlink()``, which does not follow the link — so a
    dangling link is still a link, which is usually what you want to know.
    """
    target = as_path(path)
    if target.is_symlink():
        return target
    if target.exists():
        raise ContentError(f"expected a {what} but found a regular path: {target}")
    raise FileNotFoundError(f"no {what} at {target}{_did_you_mean(target)}")


def _quote_line(text: str, lineno: int) -> str:
    """The offending source line, with its number — context for a parse error."""
    lines = text.splitlines()
    if not 1 <= lineno <= len(lines):
        return ""
    return f"\n  {lineno} | {lines[lineno - 1]}"



# Functions, layer 2: Text files

def expect_yaml(path: path_like, *, what: str = "YAML file") -> SystemPath:
    """Require a YAML file, identified by its suffix."""
    return expect_file(path, what=what, allow_empty=False, file_type=FileType.YAML)



def expect_text(path: path_like, *, what: str = "text file") -> SystemPath:
    """Require a file whose bytes decode as UTF-8 and contain no NUL byte."""
    return expect_file(path, what=what, allow_empty=False, file_type=FileType.TEXT)


def expect_markdown(path: path_like, *, what: str = "Markdown file") -> SystemPath:
    """Require a Markdown file, identified by its suffix."""
    return expect_file(path, what=what, allow_empty=False, file_type=FileType.MARKDOWN)


def expect_script(path: path_like, *, what: str = "script") -> SystemPath:
    """Require a script, identified by its suffix (``.py``, ``.sh``, …)."""
    return expect_file(path, what=what, allow_empty=False, file_type=FileType.SCRIPT)


# Functions, layer 2: Binary files


def expect_binary(path: path_like, *, what: str = "binary file") -> SystemPath:
    """Require a file that is *not* decodable text."""
    return expect_file(path, what=what, allow_empty=False, file_type=FileType.BINARY)


def expect_archive(path: path_like, *, what: str = "archive") -> SystemPath:
    """Require a readable zip archive, checked by magic number rather than name.

    This is the guard that catches a truncated download called ``pack.zip`` —
    the case where knowing the file exists tells you the least.
    """
    return expect_file(path, what=what, allow_empty=False, file_type=FileType.ARCHIVE)


def expect_executable(path: path_like, *, what: str = "executable") -> SystemPath:
    """Require a file the current user may execute."""
    return expect_file(path, what=what, file_type=FileType.EXECUTABLE)


# Functions, layer 3: JSON files


def expect_json(path: path_like, *, what: str = "JSON file") -> Any:
    """Read and parse a JSON file, raising with the offending line on failure.

    Returns the parsed document — so the check and the read are one step, and
    there is no way to accidentally use an unvalidated file.
    """
    target = expect_file(path, what=what, allow_empty=False)
    text = target.read_text(encoding="utf-8")
    try:
        return json.loads(text)
    except json.JSONDecodeError as error:
        raise ContentError(
            f"{what} is not valid JSON: {target}\n"
            f"  {error.msg} (line {error.lineno}, column {error.colno})"
            f"{_quote_line(text, error.lineno)}"
        ) from None


def expect_yaml_document(path: path_like, *, what: str = "YAML file") -> Any:
    """Read and parse a YAML file, raising with the offending line on failure.

    The layer-two :func:`expect_yaml` only checks the suffix, which is all a
    name can tell you. This actually parses, so a file that *is* called
    ``.yaml`` but is not YAML is caught here rather than by whatever tries to
    use the result.

    Uses ``safe_load``: a configuration file is data, and should never be able
    to construct arbitrary Python objects.
    """
    target = expect_file(path, what=what, allow_empty=False, file_type=FileType.YAML)
    text = target.read_text(encoding="utf-8")
    try:
        return yaml.loads(text)
    except yaml.YAMLError as error:
        mark = getattr(error, "problem_mark", None)
        where = f" (line {mark.line + 1}, column {mark.column + 1})" if mark else ""
        problem = getattr(error, "problem", None) or str(error).splitlines()[0]
        raise ContentError(
            f"{what} is not valid YAML: {target}\n  {problem}{where}"
            + (_quote_line(text, mark.line + 1) if mark else "")
        ) from None


def expect_yaml_mapping(path: path_like, *, what: str = "YAML file") -> dict[str, Any]:
    """Like :func:`expect_yaml_document`, but require a mapping at the top level.

    Configuration files are mappings; a bare list or scalar is a mistake worth
    naming, and naming it here beats a ``AttributeError`` three frames away.
    """
    document = expect_yaml_document(path, what=what)
    if not isinstance(document, dict):
        kind = "nothing" if document is None else type(document).__name__
        raise ContentError(
            f"{what} should hold a YAML mapping, but holds {kind}: {as_path(path)}"
        )
    return document


def expect_json_object(path: path_like, *, what: str = "JSON file") -> dict[str, Any]:
    """Like :func:`expect_json`, but also require the document to be an object.

    Every datapack JSON — ``pack.mcmeta``, a tag, a dialog — is an object at the
    top level, so a bare list or string is a mistake worth naming.
    """
    document = expect_json(path, what=what)
    if not isinstance(document, dict):
        kind = type(document).__name__
        raise ContentError(
            f"{what} should hold a JSON object, but holds a {kind}: {as_path(path)}"
        )
    return document

def expect(
    file_type: FileType,
    path: path_like,
    *,
    what: str | None = None,
) -> SystemPath:
    """Single-function interface: map a :class:`FileType` to the right guard.

    For when the kind is a *variable* rather than something known at the call
    site — reading it from configuration, say, or looping over several::

        for kind, candidate in ((FileType.ARCHIVE, pack), (FileType.MARKDOWN, notes)):
            expect(kind, candidate)

    Returns the path, like every guard it delegates to, so it drops into an
    expression. Raises the same exceptions they do.
    """
    label = what if what is not None else file_type.describe()

    match file_type:
        # layer one — structural
        case FileType.DIRECTORY:
            return expect_directory(path, what=label)
        case FileType.FILE:
            return expect_file(path, what=label)
        case FileType.LINK:
            return expect_link(path, what=label)
        # layer two — text
        case FileType.TEXT:
            return expect_text(path, what=label)
        case FileType.MARKDOWN:
            return expect_markdown(path, what=label)
        case FileType.SCRIPT:
            return expect_script(path, what=label)
        # layer two — binary
        case FileType.BINARY:
            return expect_binary(path, what=label)
        case FileType.ARCHIVE:
            return expect_archive(path, what=label)
        case FileType.EXECUTABLE:
            return expect_executable(path, what=label)
        case FileType.YAML:
            return expect_yaml(path, what=label)

# A `with` block was considered for these guards and deliberately not added.
#
# A context manager earns its place when there is something to acquire and
# something to release — `Config` has exactly that (load, then save on a clean
# exit), which is why it has one. These functions have neither: they inspect a
# path and either return it or raise. Wrapping that in `with` would add a scope
# with no meaning at its edges, and hide the raise inside a block that looks
# like it manages something.
#
# The thing that *would* be useful — "check several paths and report all the
# failures at once" — is a different shape, and would be a function taking a
# list, not a context manager.
