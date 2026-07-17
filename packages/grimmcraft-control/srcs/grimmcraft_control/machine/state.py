"""The :class:`State` primitive — an immutable node in the machine."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from grimmcraft_control.machine.command import Command
from grimmcraft_control.machine.event import Event


@dataclass(frozen=True, slots=True)
class State:
    """A node identified by ``name``, with declarative enter/exit/cycle commands.

    ``enter``/``exit`` are static :class:`Command` tuples: they are returned
    verbatim by the pure :meth:`on_enter`/:meth:`on_exit` hooks at runtime *and*
    read directly by the compiler when lowering the state to ``mcfunction``.
    ``cycle`` is the state's *per-tick processing loop* — commands run every game
    tick while the machine sits in this state; the compiler emits them into the
    machine's ``tick`` function, followed by the state's automatic (``"tick"``)
    transitions, which are therefore checked *after* the cycle commands each
    tick.  Keeping all of these declarative (rather than arbitrary callables) is
    what makes a state compilable.  ``is_final`` marks a terminal state; equality
    is by ``name`` so a state can be looked up by identity.
    """

    name: str
    is_final: bool = False
    enter: tuple[Command, ...] = ()
    exit: tuple[Command, ...] = ()
    cycle: tuple[Command, ...] = ()

    def on_enter(self, ctx: Any, event: Event | None) -> list[Command]:
        """Pure hook: commands to run when the machine enters this state."""
        return list(self.enter)

    def on_exit(self, ctx: Any, event: Event | None) -> list[Command]:
        """Pure hook: commands to run when the machine leaves this state."""
        return list(self.exit)

    def on_cycle(self, ctx: Any) -> list[Command]:
        """Pure hook: commands to run every tick while in this state."""
        return list(self.cycle)
