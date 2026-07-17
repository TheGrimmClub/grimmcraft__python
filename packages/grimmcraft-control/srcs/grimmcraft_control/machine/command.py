"""The :class:`Command` primitive plus a tiny synchronous execution layer.

A :class:`Command` is a *declarative description of a side effect* (the Command
pattern): it names an operation and carries a payload, but never runs anything
itself.  The machine only ever **produces** commands; a separate handler layer
(the :class:`CommandBus`) turns them into real effects.  Keeping the two apart is
what lets the machine stay pure and unit-testable — and it is exactly what lets
the compiler treat commands as data and lower them to ``mcfunction`` lines.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


@dataclass(frozen=True, slots=True)
class Command:
    """A named, declarative side effect with an arbitrary data ``payload``.

    ``name`` is a stable verb (``"say"``, ``"setblock"``, ``"summon"``, …); the
    ``payload`` holds its arguments.  Values are plain data — strings, ints,
    tuples — or ``grimmcraft_data`` enum members (``Block``/``Item``/``Entity``);
    the compiler validates whichever it finds.  Immutable value object.
    """

    name: str
    payload: Mapping[str, Any] = field(default_factory=dict)

    def with_payload(self, **extra: Any) -> Command:
        """Return a copy with ``extra`` merged over the existing payload."""
        merged = {**self.payload, **extra}
        return Command(self.name, merged)


@runtime_checkable
class CommandHandler(Protocol):
    """Anything that can perform one command type against a context."""

    def handle(self, command: Command, ctx: Any) -> None:
        """Execute ``command`` (perform its side effect) using ``ctx``."""
        ...


class CommandBus:
    """Maps command names to handlers and dispatches them synchronously.

    Used by callers and examples — never by the machine itself, which only
    computes commands.  Register a handler per command name, then feed the
    commands from a :class:`~.result.Result` through :meth:`run`.
    """

    def __init__(self) -> None:
        self._handlers: dict[str, CommandHandler] = {}

    def register(self, name: str, handler: CommandHandler) -> CommandBus:
        """Bind ``name`` to ``handler`` and return ``self`` for chaining."""
        self._handlers[name] = handler
        return self

    def run(self, commands: list[Command], ctx: Any) -> None:
        """Dispatch each command in order; unknown names raise ``KeyError``."""
        for command in commands:
            self._handlers[command.name].handle(command, ctx)
