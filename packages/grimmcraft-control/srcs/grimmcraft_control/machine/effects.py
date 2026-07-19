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


def tellraw(text: Any, *, target: str = "@a") -> Command:
    """Send ``text`` as a formatted message to ``target``.

    ``text`` is a plain ``str`` or a ``grimmcraft_core.text.Text`` component —
    the latter when it needs colour, styling or a click action.
    """
    return Command(CommandName.TELLRAW, {"text": text, "target": target})


def playsound(sound: str, *, source: str = "master", target: str = "@a") -> Command:
    """Play the ``sound`` event for ``target``."""
    return Command(
        CommandName.PLAYSOUND, {"sound": sound, "source": source, "target": target}
    )


def particle(name: str, pos: Any) -> Command:
    """Spawn the ``name`` particle at ``pos``."""
    return Command(CommandName.PARTICLE, {"particle": name, "pos": pos})


def place(structure: Any, pos: Any = None, *, rotation: str | None = None,
          mirror: str | None = None) -> Command:
    """Place a saved structure template at ``pos`` (Minecraft's ``place template``).

    ``structure`` is a ``ns:name`` template id — the file living at
    ``data/<ns>/structures/<name>.nbt`` — or anything with a ``string_id``.
    ``rotation`` is ``none``/``clockwise_90``/``180``/``counterclockwise_90`` and
    ``mirror`` is ``none``/``front_back``/``left_right``, matching the command.

    Requires Minecraft 1.19+, where ``place template`` replaced the older
    ``/structure load``.
    """
    payload: dict[str, Any] = {"structure": structure, "min_version": "1.19"}
    if pos is not None:
        payload["pos"] = pos
    if rotation is not None:
        payload["rotation"] = rotation
    if mirror is not None:
        payload["mirror"] = mirror
    return Command(CommandName.PLACE, payload)


def dialog_show(dialog: Any, *, target: str = "@s") -> Command:
    """Open the ``ns:name`` dialog screen for ``target`` (Minecraft 1.21.6+).

    Dialogs are a vanilla datapack registry (``data/<ns>/dialog/<name>.json``)
    that renders a real UI with buttons — the modern way to offer a player a
    choice, replacing a wall of clickable chat lines.
    """
    return Command(
        CommandName.DIALOG_SHOW,
        {"dialog": dialog, "target": target, "min_version": "1.21.6"},
    )


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


def if_score(objective: str, entry: str, value: int, then: Command) -> Command:
    """Run ``then`` only when ``entry``'s ``objective`` score equals ``value``.

    Renders as ``execute if score … run <then>``. Handy inside a state's cycle to
    do a different thing on each tick/stage (e.g. place stage N's blocks only when
    a counter reaches N)."""
    return Command(
        "execute_if_score",
        {"objective": objective, "entry": entry, "value": value, "run": then},
    )
