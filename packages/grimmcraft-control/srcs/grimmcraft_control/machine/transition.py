"""The :class:`Transition` primitive plus its guard/condition helpers."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from typing import Any

from grimmcraft_control.machine.command import Command
from grimmcraft_control.machine.event import Event

#: A pure predicate deciding whether a transition may fire at runtime.
Guard = Callable[[Any, Event], bool]

#: A pure function returning the commands a transition contributes at runtime.
Action = Callable[[Any, Event], list[Command]]


@dataclass(frozen=True, slots=True)
class Condition:
    """A *declarative* guard the compiler can lower to an ``execute if`` clause.

    Runtime guards are arbitrary Python callables and cannot be compiled; a
    ``Condition`` names a statically analysable check (e.g.
    ``Condition("score_matches", {"objective": ..., "value": 1})``) so the same
    transition can be both driven in Python and emitted as a command.
    """

    name: str
    payload: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class Transition:
    """An edge ``(source, event) -> target`` with optional guard and effects.

    ``guard``/``action`` are the pure runtime callables.  ``commands`` is the
    static, compilable list of effects, and ``condition`` is the static,
    compilable guard.  A transition may carry both a runtime ``guard`` and a
    declarative ``condition``; the machine uses the former, the compiler the
    latter.  Immutable.
    """

    source: str
    event: str
    target: str
    guard: Guard | None = None
    action: Action | None = None
    commands: tuple[Command, ...] = ()
    condition: Condition | None = None

    def run_action(self, ctx: Any, event: Event) -> list[Command]:
        """Commands this transition contributes: the ``action`` if given, else
        the static ``commands``."""
        if self.action is not None:
            return self.action(ctx, event)
        return list(self.commands)
