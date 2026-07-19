"""Guards that fail *usefully* — ``expect_file``, ``expect_dir``, ``expect_json``.

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
"""

# [ ] Includes standard
import difflib
import json
from typing import Any

# [ ] Includes internal
from grimmclub_filesystem.core import SystemPath, path_like
from grimmclub_filesystem.paths import as_path

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


def expect_file(path: path_like, *, what: str = "file", allow_empty: bool = True) -> SystemPath:
    """Return ``path`` as a :class:`SystemPath`, or raise explaining why not.

    ``what`` names the thing for the message ("structure file", "preset").  With
    ``allow_empty=False`` a zero-byte file is rejected too — it usually means a
    write failed halfway rather than that the file is genuinely absent.
    """
    target = as_path(path)
    if target.is_file():
        if not allow_empty and target.stat().st_size == 0:
            raise ContentError(f"{what} is empty: {target}")
        return target

    if target.is_dir():
        raise IsADirectoryError(f"expected a {what} but found a directory: {target}")
    if not target.parent.exists():
        raise FileNotFoundError(
            f"no {what} at {target}\n  the folder {target.parent} does not exist"
        )
    raise FileNotFoundError(f"no {what} at {target}{_did_you_mean(target)}")


def expect_dir(path: path_like, *, what: str = "directory") -> SystemPath:
    """Return ``path`` as a :class:`SystemPath` directory, or raise."""
    target = as_path(path)
    if target.is_dir():
        return target
    if target.is_file():
        raise NotADirectoryError(f"expected a {what} but found a file: {target}")
    raise FileNotFoundError(f"no {what} at {target}{_did_you_mean(target)}")


def _quote_line(text: str, lineno: int) -> str:
    """The offending source line, with its number — context for a parse error."""
    lines = text.splitlines()
    if not 1 <= lineno <= len(lines):
        return ""
    return f"\n  {lineno} | {lines[lineno - 1]}"


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
