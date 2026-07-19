"""``json``, but the four common calls debug-log what they (de)serialise.

Same API as the stdlib :mod:`json` — ``dumps`` / ``loads`` / ``dump`` / ``load``
delegate to it and add a :func:`~grimmclub.log.debug` line — and everything else
(``JSONDecodeError``, ``JSONEncoder``, …) is forwarded unchanged, so
``grimmclub.json`` is a drop-in replacement.
"""

from __future__ import annotations

# Includes standard
import json as _json
from typing import Any

# Includes internal
from grimmclub_standardlib.log import debug


def dumps(obj: Any, **kwargs: Any) -> str:
    """Serialise ``obj`` to a JSON string (logs its length in debug mode)."""
    text = _json.dumps(obj, **kwargs)
    debug("json.dumps", f"-> {len(text)} chars")
    return text


def loads(s: str | bytes, **kwargs: Any) -> Any:
    """Parse a JSON string/bytes (logs its length in debug mode)."""
    debug("json.loads", f"<- {len(s)} chars")
    return _json.loads(s, **kwargs)


def dump(obj: Any, fp: Any, **kwargs: Any) -> None:
    """Serialise ``obj`` to the open file ``fp``."""
    debug("json.dump ->", getattr(fp, "name", fp))
    _json.dump(obj, fp, **kwargs)


def load(fp: Any, **kwargs: Any) -> Any:
    """Parse JSON from the open file ``fp``."""
    debug("json.load <-", getattr(fp, "name", fp))
    return _json.load(fp, **kwargs)


def __getattr__(name: str) -> Any:
    """Forward everything else (JSONDecodeError, JSONEncoder, …) to stdlib json."""
    return getattr(_json, name)
