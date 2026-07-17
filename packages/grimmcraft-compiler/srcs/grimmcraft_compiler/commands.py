"""Constructors for the command vocabulary the :class:`~.dialect.Dialect` renders.

Machine effects arrive as :class:`grimmcraft_control.machine.Command` objects
(``say``, ``setblock``, ``give`` …).  Lowering also needs a handful of
*compiler-internal* commands (calling a function, guarding on a score, setting
the state score); those are plain :class:`Command`\\ s too, built by the helpers
here so the lowering code reads declaratively and the Dialect has a single render
table to implement.
"""

from __future__ import annotations

from typing import Any

from grimmcraft_control.machine import Command

# --- names the Dialect must know how to render -------------------------------

#: Domain effect command names produced by machines.
DOMAIN_COMMANDS = frozenset(
    {"say", "tellraw", "setblock", "summon", "give", "playsound", "particle", "raw"}
)

#: Compiler-internal command names produced by lowering.
INTERNAL_COMMANDS = frozenset(
    {
        "call",
        "comment",
        "scoreboard_set",
        "scoreboard_add",
        "scoreboard_objective_add",
        "execute_if_score",
    }
)

#: Everything the Dialect renders.
KNOWN_COMMANDS = DOMAIN_COMMANDS | INTERNAL_COMMANDS


def call(ref: str) -> Command:
    """Call another function by ``ns:path`` id."""
    return Command("call", {"ref": ref})


def comment(text: str) -> Command:
    """A ``# comment`` line (kept in the IR for readable generated functions)."""
    return Command("comment", {"text": text})


def scoreboard_objective_add(objective: str, criterion: str = "dummy") -> Command:
    """Declare a scoreboard objective (idempotent at runtime)."""
    return Command("scoreboard_objective_add",
                   {"objective": objective, "criterion": criterion})


def scoreboard_set(objective: str, entry: str, value: int) -> Command:
    """Set ``entry``'s score under ``objective`` to ``value``."""
    return Command("scoreboard_set",
                   {"objective": objective, "entry": entry, "value": value})


def execute_if_score(
    objective: str, entry: str, value: int, run: Command
) -> Command:
    """Run ``run`` only if ``entry``'s ``objective`` score equals ``value``."""
    return Command(
        "execute_if_score",
        {"objective": objective, "entry": entry, "value": value, "run": run},
    )


def raw(text: str) -> Command:
    """A raw, pre-rendered command line (escape hatch / passthrough)."""
    return Command("raw", {"text": text})


def payload_get(command: Command, key: str, default: Any = None) -> Any:
    """Convenience accessor for a command payload value."""
    return command.payload.get(key, default)
