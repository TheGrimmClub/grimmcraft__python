"""Game session state: the roster of players, their game modes, and the rules.

# Classes:

- `GameModeType`: survival, creative, adventure, spectator
- `Game()`: a session — players, their modes, and the world's game rules

Modes and rules are *keyed* (by player / rule), so they are exposed as accessor
methods rather than properties: a Python ``property`` cannot take a key.

# Game rules

:class:`~grimmcraft_data.game_rule.GameRule` comes from ``grimmcraft-data``,
generated from Mojang's own translation keys. It replaced a hand-written enum
with one member spelled ``do_daylight_cycle``, whose own TODO admitted the
author had guessed at snake_case. None of the 63 real rules contain an
underscore, and ``/gamerule do_daylight_cycle true`` is not rejected by the game
— it is silently ignored, which is the worst way to be wrong.

Accessors take the enum rather than a string, which is what makes the enum worth
having: ``set_rule("doDayLightCycle", True)`` used to type-check and quietly
create a rule that did nothing.

**Values are ``bool`` or ``int``.** Those are the only two kinds Minecraft has;
there is no string or float rule, so a wider type would let
``set_rule(rule, 3.7)`` pass here and fail in game.

**An unset rule reads as ``None``.** Every rule does have a vanilla default, but
that default is in none of the data files this package ships, so inventing one
would be worse than admitting there is none — the same reason core ships no
recipes. Pass ``default=`` when the caller has an opinion.
"""

from __future__ import annotations

# Includes standard
from grimmclub_standardlib import Enum

# Includes internal
from grimmcraft_data.game_rule import GameRule


# Types
class GameModeType(Enum):
    """A Minecraft game mode.

    Named ``…Type`` to match the other registry enums re-exported from
    ``grimmcraft-data``. :class:`~grimmcraft_core.entity.player.Player` uses
    this one; it previously carried a second, identical enum of its own.
    """

    SURVIVAL = "survival"
    CREATIVE = "creative"
    ADVENTURE = "adventure"
    SPECTATOR = "spectator"


# Main Class
class Game:
    """A game session: a roster of players, each with a game mode, plus rules.

    The synthetic ``core`` player seeds the default mode new players inherit.
    """

    core: str = "core"

    def __init__(self) -> None:
        self._players: list[str] = [self.core]
        self._mode: dict[str, GameModeType] = {self.core: GameModeType.SURVIVAL}
        self._rule: dict[GameRule, bool | int] = {}
        self._banned: set[str] = set()

    def __str__(self) -> str:
        return f"Game(players={len(self._players)}, rules={len(self._rule)})"

    # --- players -------------------------------------------------------------
    def has_player(self, player: str) -> bool:
        """Whether ``player`` is currently on the roster."""
        return player in self._players

    def add_player(self, player: str) -> None:
        """Add ``player``, inheriting the default (``core``) game mode.

        A banned player is refused; unban them first.
        """
        if player in self._banned:
            raise ValueError(f"{player} is banned; unban them before adding")
        if not self.has_player(player):
            self._players.append(player)
            self._mode[player] = self._mode[self.core]

    def remove_player(self, player: str) -> None:
        """Remove ``player`` from the roster (no-op if absent)."""
        if self.has_player(player):
            self._players.remove(player)
            del self._mode[player]

    def ban_player(self, player: str) -> None:
        """Remove ``player`` and refuse to let them back in.

        Distinct from :meth:`remove_player`, which it used to simply call — a
        ban that forgot the player was a ban only until they reconnected.
        """
        self.remove_player(player)
        self._banned.add(player)

    def unban_player(self, player: str) -> None:
        """Lift a ban (no-op if there was none). Does not re-add the player."""
        self._banned.discard(player)

    def is_banned(self, player: str) -> bool:
        """Whether ``player`` is barred from being added."""
        return player in self._banned

    @property
    def players(self) -> list[str]:
        """The roster, including the synthetic ``core`` seed player."""
        return list(self._players)

    # --- game rules ----------------------------------------------------------
    def rule(self, name: GameRule, default: bool | int | None = None) -> bool | int | None:
        """The current value of ``name``, or ``default`` when it was never set.

        Returns ``None`` rather than raising for an unset rule: a rule nobody
        set is a question with an answer, not an error. It used to raise
        :class:`KeyError`, so reading any rule on a fresh session failed.
        """
        return self._rule.get(name, default)

    def set_rule(self, name: GameRule, value: bool | int) -> None:
        """Set ``name`` to ``value`` — ``bool`` or ``int``, the only two kinds."""
        self._rule[name] = value

    def is_rule_set(self, name: GameRule) -> bool:
        """Whether ``name`` has been given a value in this session."""
        return name in self._rule

    @property
    def rules(self) -> dict[GameRule, bool | int]:
        """Every rule set in this session, as a copy."""
        return dict(self._rule)

    # --- game modes ----------------------------------------------------------
    def mode(self, player: str | None = None) -> GameModeType:
        """The game mode of ``player`` (defaults to the ``core`` seed player)."""
        key = self.core if player is None else player
        if not self.has_player(key):
            raise ValueError(f"Player {key} not found")
        return self._mode[key]

    def set_mode(self, player: str, mode: GameModeType) -> None:
        """Set ``player``'s game mode.

        Rejects an unknown player, matching :meth:`mode`: setting a mode for
        someone not on the roster used to succeed and then be lost.
        """
        if not self.has_player(player):
            raise ValueError(f"Player {player} not found")
        self._mode[player] = mode
