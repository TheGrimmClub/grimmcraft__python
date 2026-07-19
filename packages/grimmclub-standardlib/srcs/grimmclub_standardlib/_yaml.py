"""``yaml``, but ``load`` is safe and the four common calls debug-log.

The companion to :mod:`grimmclub_standardlib._json`, with the same four calls —
``dumps`` / ``loads`` / ``dump`` / ``load`` — so a lesson that reads JSON reads
YAML the same way, and everything else is forwarded to PyYAML unchanged.

# Two deliberate differences from PyYAML

**``load`` here means ``safe_load``.** PyYAML's own ``yaml.load`` can construct
arbitrary Python objects from a document, so reading an untrusted file can run
code. That is a genuine footgun, and a package meant for people learning the
language should not ship it as the obvious call. Every caller in this workspace
already used ``safe_load``, so nothing changes but the name. When the full
loader really is wanted -- a document with custom tags -- ask for it by name via
:func:`unsafe_load`, where the reader can see the choice was made.

**``dump`` defaults to ``sort_keys=False``.** PyYAML reorders mappings
alphabetically by default, which turns a hand-written configuration file into a
scrambled one the first time a program rewrites it. Keeping insertion order
makes a saved file look like the file the trainee wrote. Pass ``sort_keys=True``
to get PyYAML's behaviour back.

# Why the import is lazy

``grimmclub-standardlib`` declares **no** dependencies, which is what lets every
other package rely on it freely, and PyYAML is not part of the standard library.
So it is imported on first use rather than at module import, and its absence
raises an explanation rather than a bare :class:`ModuleNotFoundError`.

Trainees never meet that path: :mod:`grimmclub`, the front door, depends on
PyYAML, so ``from grimmclub import yaml`` always works. The lazy import exists
for the *libraries* underneath, which stay dependency-free.
"""

from __future__ import annotations

from typing import Any

from grimmclub_standardlib.log import debug

_MISSING = (
    "PyYAML is not installed, so YAML support is unavailable.\n"
    "  grimmclub-standardlib declares no dependencies on purpose, so YAML is optional here.\n"
    "  Install it with 'uv add pyyaml', or import from 'grimmclub', which always provides it."
)


def _yaml() -> Any:
    """Import PyYAML on first use, explaining itself if it is not installed."""
    try:
        import yaml
    except ModuleNotFoundError as error:  # pragma: no cover - depends on install
        raise ModuleNotFoundError(_MISSING) from error
    return yaml


def dumps(obj: Any, **kwargs: Any) -> str:
    """Serialise ``obj`` to a YAML string, keeping key order (logs its length)."""
    kwargs.setdefault("sort_keys", False)
    text: str = _yaml().safe_dump(obj, **kwargs)
    debug("yaml.dumps", f"-> {len(text)} chars")
    return text


def loads(text: str | bytes, **kwargs: Any) -> Any:
    """Parse a YAML string/bytes with the **safe** loader (logs its length)."""
    debug("yaml.loads", f"<- {len(text)} chars")
    return _yaml().safe_load(text, **kwargs)


def dump(obj: Any, fp: Any, **kwargs: Any) -> None:
    """Serialise ``obj`` to the open file ``fp``, keeping key order."""
    kwargs.setdefault("sort_keys", False)
    debug("yaml.dump ->", getattr(fp, "name", fp))
    _yaml().safe_dump(obj, fp, **kwargs)


def load(fp: Any, **kwargs: Any) -> Any:
    """Parse YAML from the open file ``fp`` with the **safe** loader."""
    debug("yaml.load <-", getattr(fp, "name", fp))
    return _yaml().safe_load(fp, **kwargs)


def unsafe_load(source: Any, **kwargs: Any) -> Any:
    """Parse YAML with the **full** loader, which can construct Python objects.

    Only for documents whose custom tags are actually needed, from a source you
    trust. :func:`load` is what you want otherwise; this one is named so that
    choosing it is visible in the code that chose it.
    """
    debug("yaml.unsafe_load <-", getattr(source, "name", "<string>"))
    return _yaml().unsafe_load(source, **kwargs)


def __getattr__(name: str) -> Any:
    """Forward everything else (YAMLError, SafeLoader, …) to PyYAML."""
    return getattr(_yaml(), name)
