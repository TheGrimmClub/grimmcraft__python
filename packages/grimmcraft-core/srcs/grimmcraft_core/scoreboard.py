"""A minimal Minecraft-style scoreboard of named integer counters."""

from __future__ import annotations


class ScoreBoard:
    """A set of integer counters keyed by name (a single scoreboard objective).

    Reading an unset counter yields 0; writing auto-creates it.  This backs
    higher-level features such as the in-world :mod:`clock`.
    """

    def __init__(self, name: str) -> None:
        self.name = name
        self._counters: dict[str, int] = {}

    def get(self, key: str) -> int:
        """The current value of ``key`` (0 if it has never been set)."""
        return self._counters.get(key, 0)

    def set(self, key: str, value: int) -> None:
        """Set ``key`` to ``value``."""
        self._counters[key] = value

    def add(self, key: str, delta: int = 1) -> int:
        """Add ``delta`` to ``key`` and return the new value."""
        self._counters[key] = self.get(key) + delta
        return self._counters[key]

    def reset(self, key: str) -> None:
        """Set ``key`` back to 0."""
        self._counters[key] = 0

    def keys(self) -> list[str]:
        """All counter names currently tracked."""
        return list(self._counters)
