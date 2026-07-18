"""The :class:`EffectWriter` behind ``state.enter`` / ``.cycle`` / ``transition.do``.

It lets you add effects as *methods on the state* — no importing ``setblock`` /
``fill`` / ``say`` and friends::

    on = builder.add_state("ON")
    on.enter.setblock(pos, Block.LIGHT, level=15)
    on.enter.say("lit!")
    on.cycle.add_score("timer", "lamp", -1)
    on.cycle.if_score("timer", "lamp", 0).fill(a, b, Block.AIR)

Each method builds one :class:`Command` (via the constructors in
:mod:`grimmcraft_control.machine.effects`) and appends it to that phase. Every
method returns the writer, so calls chain. You can still pass ready-made commands
by calling the writer directly: ``on.enter(some_command)``.
"""

from __future__ import annotations

from typing import Any

from grimmcraft_control.machine import effects
from grimmcraft_control.machine.command import Command


class EffectWriter:
    """Appends effect commands to one phase's command list."""

    def __init__(self, sink: list[Command]) -> None:
        self._sink = sink

    def _add(self, command: Command) -> EffectWriter:
        self._sink.append(command)
        return self

    def __call__(self, *commands: Command) -> EffectWriter:
        """Append ready-made :class:`Command`\\ s (the escape hatch)."""
        for command in commands:
            self._add(command)
        return self

    # --- effect methods (mirror grimmcraft_control.machine.effects) ----------
    def setblock(self, pos: Any, block: Any, **state: Any) -> EffectWriter:
        """Place ``block`` at ``pos`` (block-state props as keyword args)."""
        return self._add(effects.setblock(pos, block, **state))

    def fill(
        self, start: Any, end: Any, block: Any, *, mode: str | None = None, **state: Any
    ) -> EffectWriter:
        """Fill the box between two corners with ``block``."""
        return self._add(effects.fill(start, end, block, mode=mode, **state))

    def say(self, text: str) -> EffectWriter:
        """Broadcast ``text`` to chat."""
        return self._add(effects.say(text))

    def tellraw(self, text: str, *, target: str = "@a") -> EffectWriter:
        """Send ``text`` as a formatted message to ``target``."""
        return self._add(effects.tellraw(text, target=target))

    def playsound(
        self, sound: str, *, source: str = "master", target: str = "@a"
    ) -> EffectWriter:
        """Play a sound event for ``target``."""
        return self._add(effects.playsound(sound, source=source, target=target))

    def particle(self, name: str, pos: Any) -> EffectWriter:
        """Spawn the ``name`` particle at ``pos``."""
        return self._add(effects.particle(name, pos))

    def summon(self, entity: Any, pos: Any | None = None) -> EffectWriter:
        """Summon ``entity`` (at ``pos``, or where the function runs)."""
        return self._add(effects.summon(entity, pos))

    def give(
        self, item: Any, *, target: str = "@p", count: int = 1, name: str | None = None
    ) -> EffectWriter:
        """Give ``count`` of ``item`` to ``target``."""
        return self._add(effects.give(item, target=target, count=count, name=name))

    def set_score(self, objective: str, entry: str, value: int) -> EffectWriter:
        """Set ``entry``'s ``objective`` score to ``value``."""
        return self._add(effects.set_score(objective, entry, value))

    def add_score(self, objective: str, entry: str, delta: int) -> EffectWriter:
        """Add ``delta`` to ``entry``'s ``objective`` score."""
        return self._add(effects.add_score(objective, entry, delta))

    def if_score(self, objective: str, entry: str, value: int) -> EffectWriter:
        """Return a writer whose next effect(s) run only when ``entry``'s
        ``objective`` score equals ``value`` (an ``execute if score`` guard)::

            state.cycle.if_score("stage", "tree", 1).fill(a, b, Block.OAK_LOG)
        """
        return _GuardedWriter(self._sink, objective, entry, value)


class _GuardedWriter(EffectWriter):
    """An :class:`EffectWriter` that wraps each command in an ``if_score`` guard."""

    def __init__(self, sink: list[Command], objective: str, entry: str, value: int) -> None:
        super().__init__(sink)
        self._objective = objective
        self._entry = entry
        self._value = value

    def _add(self, command: Command) -> EffectWriter:
        self._sink.append(
            effects.if_score(self._objective, self._entry, self._value, command)
        )
        return self
