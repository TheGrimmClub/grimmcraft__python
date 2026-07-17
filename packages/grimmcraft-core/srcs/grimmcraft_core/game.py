"""
- manage the `gamemode` and `gamerules` via a class interface
- manage a list of players (online and offline)

"""

from typing import Any
from enum import Enum


class GameModeType(Enum):
    SURVIVAL = "survival"
    CREATIVE = "creative"
    ADVENTURE = "adventure"
    SPECTATOR = "spectator"

class GameRulesType(Enum):
    DO_DAYLIGHT_CYCLE = "doDaylightCycle"





class Game:
    core: str = 'core'
    def __init__(self) -> None:
        self._players: list = [self.core]
        self._mode: dict[str,GameModeType] = {self.core: GameModeType.SURVIVAL }
        self._rule: dict[str,Any] = {}

    def __str__(self) -> str:
        pass

    def has_player(self, player: str) -> bool:
        return player in self._players

    def add_player(self, player: str) -> None:
        if not self.has_player(player):
            self._players.append(player)
            self._mode[player] = self.mode[self.core]

    def ban_player(self, player: str) -> None:
        if self.has_player(player):
            self._players.remove(player)
            del self._mode[player]

    def remove_player(self, player: str) -> None:
        if self.has_player(player):
            self._players.remove(player)
            del self._mode[player]

    @property
    def rule(self, name: str) -> Any:
        return self._rule[name]

    @rule.setter
    def set_rule(self, name: str, value: Any) -> None:
        self._rule[name] = value

    @property
    def mode(self, player: str = self.core) -> Any:
        if not self.has_player(player):
            raise ValueError(f"Player {player} not found")
        return self._mode[player]

    @mode.setter
    def set_mode(self, player: str, mode: Any) -> None:
        self._mode[player] = mode
