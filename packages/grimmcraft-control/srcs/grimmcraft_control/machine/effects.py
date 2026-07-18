"""Beginner-friendly constructors for the common commands.

Instead of hand-writing a command name and a payload dict::

    Command(CommandName.SETBLOCK, {"pos": p, "block": b, "state": {"level": "15"}})

call a small typed function::

    setblock(p, b, level=15)

Each returns a plain :class:`Command`, so it drops straight into a state's
``on_enter`` / ``on_cycle`` or a transition's ``do(...)``. ``block``/``item``
accept a ``grimmcraft_data`` enum member *or* a namespaced string; ``pos`` accepts
a ``grimmcraft_core`` ``BlockPos``/``Coordinates``, an ``(x, y, z)`` tuple, or a
raw ``"~ ~ ~"`` string.
"""

from __future__ import annotations

from typing import Any

from grimmcraft_control.machine.command import Command
from grimmcraft_control.machine.vocabulary import CommandName


def setblock(pos: Any, block: Any, **state: Any) -> Command:
    """Place ``block`` at ``pos``; block-state props are keyword args
    (``setblock(p, Block.LIGHT, level=15)``)."""
    payload: dict[str, Any] = {"pos": pos, "block": block}
    if state:
        payload["state"] = {key: str(value) for key, value in state.items()}
    return Command(CommandName.SETBLOCK, payload)


def fill(start: Any, end: Any, block: Any, *, mode: str | None = None, **state: Any) -> Command:
    """Fill the box between two corners with ``block`` (Minecraft ``fill``).

    This is the right tool for a run of blocks — a column, a slab, a wall — instead
    of one ``setblock`` per cell. ``mode`` is an optional ``fill`` mode such as
    ``"keep"`` (only replace air) or ``"destroy"``; block-state props are keyword
    args, as with :func:`setblock`.
    """
    payload: dict[str, Any] = {"from": start, "to": end, "block": block}
    if state:
        payload["state"] = {key: str(value) for key, value in state.items()}
    if mode is not None:
        payload["mode"] = mode
    return Command(CommandName.FILL, payload)


def say(text: str) -> Command:
    """Broadcast ``text`` to chat (the ``say`` command)."""
    return Command(CommandName.SAY, {"text": text})


def tellraw(text: str, *, target: str = "@a") -> Command:
    """Send ``text`` as a formatted message to ``target``."""
    return Command(CommandName.TELLRAW, {"text": text, "target": target})


def playsound(sound: str, *, source: str = "master", target: str = "@a") -> Command:
    """Play the ``sound`` event for ``target``."""
    return Command(
        CommandName.PLAYSOUND, {"sound": sound, "source": source, "target": target}
    )


def particle(name: str, pos: Any) -> Command:
    """Spawn the ``name`` particle at ``pos``."""
    return Command(CommandName.PARTICLE, {"particle": name, "pos": pos})


def summon(entity: Any, pos: Any | None = None) -> Command:
    """Summon ``entity`` (at ``pos``, or where the function runs)."""
    payload: dict[str, Any] = {"entity": entity}
    if pos is not None:
        payload["pos"] = pos
    return Command(CommandName.SUMMON, payload)


def give(item: Any, *, target: str = "@p", count: int = 1, name: str | None = None) -> Command:
    """Give ``count`` of ``item`` to ``target``, optionally with a custom ``name``."""
    payload: dict[str, Any] = {"item": item, "target": target, "count": count}
    if name is not None:
        payload["name"] = name
    return Command(CommandName.GIVE, payload)


def set_score(objective: str, entry: str, value: int) -> Command:
    """Set ``entry``'s ``objective`` score to ``value``."""
    return Command(
        CommandName.SCOREBOARD_SET,
        {"objective": objective, "entry": entry, "value": value},
    )


def add_score(objective: str, entry: str, delta: int) -> Command:
    """Add ``delta`` to ``entry``'s ``objective`` score."""
    return Command(
        CommandName.SCOREBOARD_ADD,
        {"objective": objective, "entry": entry, "value": delta},
    )
