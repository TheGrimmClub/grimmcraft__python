"""Game session state: the :class:`Game` tracks players plus their per-player
game mode and the world's game rules through a small class interface.

Modes and rules are *keyed* (by player / rule name), so they are exposed as
accessor methods rather than properties — a Python ``property`` cannot take a
key argument.
"""

# Includes
from __future__ import annotations

from grimmclub_standardlib import Any, Enum


# Types
class GameModeType(Enum):
    """A Minecraft game mode."""

    SURVIVAL = "survival"
    CREATIVE = "creative"
    ADVENTURE = "adventure"
    SPECTATOR = "spectator"

#
class GameRulesType(Enum):
    """A supported game rule key."""

    DO_DAYLIGHT_CYCLE = "do_daylight_cycle"
    # TODO: add other game rules
    # TODO: ensure the correct writing (i assume it is snake case)

# Class
class Game:
    """A game session: a roster of players, each with a game mode, plus rules.

    The synthetic ``core`` player seeds the default mode new players inherit.
    """

    core: str = "core"

    def __init__(self) -> None:
        self._players: list[str] = [self.core]
        self._mode: dict[str, GameModeType] = {self.core: GameModeType.SURVIVAL}
        self._rule: dict[str, Any] = {}

    def __str__(self) -> str:
        return f"Game(players={len(self._players)}, rules={len(self._rule)})"

    # --- players -------------------------------------------------------------
    def has_player(self, player: str) -> bool:
        """Whether ``player`` is currently on the roster."""
        return player in self._players

    def add_player(self, player: str) -> None:
        """Add ``player``, inheriting the default (``core``) game mode."""
        if not self.has_player(player):
            self._players.append(player)
            self._mode[player] = self._mode[self.core]

    def ban_player(self, player: str) -> None:
        """Remove ``player`` and forget their mode."""
        self.remove_player(player)

    def remove_player(self, player: str) -> None:
        """Remove ``player`` from the roster (no-op if absent)."""
        if self.has_player(player):
            self._players.remove(player)
            del self._mode[player]

    # --- game rules ----------------------------------------------------------
    def rule(self, name: str) -> Any:
        """The current value of game rule ``name``."""
        return self._rule[name]

    def set_rule(self, name: str, value: Any) -> None:
        """Set game rule ``name`` to ``value``."""
        self._rule[name] = value

    # --- game modes ----------------------------------------------------------
    def mode(self, player: str | None = None) -> GameModeType:
        """The game mode of ``player`` (defaults to the ``core`` seed player)."""
        key = self.core if player is None else player
        if not self.has_player(key):
            raise ValueError(f"Player {key} not found")
        return self._mode[key]

    def set_mode(self, player: str, mode: GameModeType) -> None:
        """Set ``player``'s game mode."""
        self._mode[player] = mode
