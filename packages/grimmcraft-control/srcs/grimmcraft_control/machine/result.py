"""The :class:`Result` primitive — the outcome of dispatching an event."""

from __future__ import annotations

from dataclasses import dataclass, field

from grimmcraft_control.machine.command import Command
from grimmcraft_control.machine.event import Event


@dataclass(frozen=True, slots=True)
class Result:
    """The immutable outcome of :meth:`Machine.dispatch`.

    Modelled after a Rust ``Result``: ``ok`` distinguishes a taken transition
    from a rejection.  On success it carries the traversed edge and the ordered
    ``commands`` collected from ``on_exit`` → action → ``on_enter``.  On a
    rejection the machine state is unchanged and ``error`` explains why.
    """

    ok: bool
    event: Event
    from_state: str
    to_state: str
    commands: list[Command] = field(default_factory=list)
    error: str | None = None

    @classmethod
    def transitioned(
        cls,
        event: Event,
        from_state: str,
        to_state: str,
        commands: list[Command],
    ) -> Result:
        """A successful transition from ``from_state`` to ``to_state``."""
        return cls(True, event, from_state, to_state, commands, None)

    @classmethod
    def rejected(cls, event: Event, state: str, reason: str) -> Result:
        """A rejected event that left the machine in ``state`` unchanged."""
        return cls(False, event, state, state, [], reason)

    def __bool__(self) -> bool:
        return self.ok
