"""Named vocabularies for command and condition kinds.

These are ``StrEnum``\\ s, so each member *is* its string value
(``CommandName.SETBLOCK == "setblock"``). That means they drop straight into
``Command("setblock", …)`` call sites — ``Command(CommandName.SETBLOCK, …)`` —
and everywhere the compiler compares, renders or looks up a command name,
without any coercion. Prefer the enum over a bare string so typos are caught and
editors can autocomplete.
"""

from __future__ import annotations

from enum import StrEnum


class CommandName(StrEnum):
    """The declarative command kinds a machine can emit."""

    SAY = "say"
    TELLRAW = "tellraw"
    SETBLOCK = "setblock"
    FILL = "fill"
    SUMMON = "summon"
    GIVE = "give"
    PLAYSOUND = "playsound"
    PARTICLE = "particle"
    PLACE = "place"
    DIALOG_SHOW = "dialog_show"
    SCOREBOARD_SET = "scoreboard_set"
    SCOREBOARD_ADD = "scoreboard_add"
    RAW = "raw"


class ConditionName(StrEnum):
    """The declarative guard kinds a transition can carry (for the compiler)."""

    SCORE_MATCHES = "score_matches"
