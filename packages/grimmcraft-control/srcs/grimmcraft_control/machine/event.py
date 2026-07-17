"""The :class:`Event` primitive — an immutable input that may trigger a transition."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class Event:
    """An input to the machine, identified by a stable ``type`` string.

    Concrete events are just values with a ``type`` and an optional typed
    ``payload`` (e.g. ``Event("insert_fuel", {"item": Item.COAL})``).  Immutable
    so events can be logged, compared and replayed freely.
    """

    type: str
    payload: Mapping[str, Any] = field(default_factory=dict)
