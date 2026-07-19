"""Level 3 — write reconstructed machines back out as builder Python.

The output is the source a person would have written: ``new_machine("lamp")``,
``add_state``, ``.enter.setblock(...)``, ``.transition(...)``, ``.when_score(...)``
— running it rebuilds an equivalent machine, and compiling *that* reproduces the
datapack.

Effects are emitted through the :class:`~grimmcraft_control.machine.writer.EffectWriter`
methods rather than raw ``Command(...)`` constructors wherever one exists, since
the whole point of this level is legibility.  A command with no writer method
falls back to passing a ``Command`` to the writer's call form, which is the
documented escape hatch and keeps even an unmodelled ``raw`` line runnable.
"""

from __future__ import annotations

import builtins
import keyword
import re
from collections.abc import Sequence
from typing import Any

from grimmcraft_control.machine import TICK_EVENT, Command, Machine
from grimmcraft_core import BlockPos

#: Characters that cannot appear in a Python identifier.
_NON_IDENTIFIER = re.compile(r"[^0-9a-zA-Z_]+")

#: Builtin names a generated variable must not shadow (``open``, ``id``, …).
_BUILTINS = frozenset(dir(builtins))


def _identifier(name: str, *, used: set[str], fallback: str = "state") -> str:
    """A unique, valid Python variable name derived from ``name``.

    Avoids keywords *and* builtins: a state called ``OPEN`` would otherwise
    shadow ``open`` in the generated module, which is legal but a trap for
    anyone who then edits the file.
    """
    candidate = _NON_IDENTIFIER.sub("_", name).strip("_").lower() or fallback
    if (
        candidate[0].isdigit()
        or keyword.iskeyword(candidate)
        or candidate in _BUILTINS
    ):
        candidate = f"{fallback}_{candidate}"
    unique = candidate
    suffix = 2
    while unique in used:
        unique = f"{candidate}_{suffix}"
        suffix += 1
    used.add(unique)
    return unique


def _literal(value: Any) -> str:
    """Render a payload value as Python source."""
    if isinstance(value, BlockPos):
        return f"BlockPos({value.x}, {value.y}, {value.z})"
    if isinstance(value, Command):
        return _command_literal(value)
    if isinstance(value, dict):
        items = ", ".join(f"{_literal(k)}: {_literal(v)}" for k, v in value.items())
        return f"{{{items}}}"
    if isinstance(value, (list, tuple)):
        items = ", ".join(_literal(item) for item in value)
        return f"[{items}]" if isinstance(value, list) else f"({items},)"
    string_id = getattr(value, "string_id", None)
    if isinstance(string_id, str):
        return repr(string_id)
    return repr(value)


def _command_literal(command: Command) -> str:
    """A ``Command(...)`` constructor call — the escape hatch for odd commands."""
    payload = ", ".join(
        f"{key!r}: {_literal(value)}" for key, value in command.payload.items()
    )
    return f"Command({str(command.name)!r}, {{{payload}}})"


def _state_kwargs(state: dict[str, str]) -> str:
    """Block-state props rendered as keyword arguments (``level=15``)."""
    return "".join(
        f", {key}={value!r}" if not _is_identifier(key) else f", {key}={value!r}"
        for key, value in state.items()
    )


def _is_identifier(name: str) -> bool:
    return name.isidentifier() and not keyword.iskeyword(name)


def _effect_call(command: Command) -> str | None:
    """The ``EffectWriter`` method call for ``command``, or ``None`` if it has none.

    Mirrors :mod:`grimmcraft_control.machine.effects` one-to-one; anything absent
    here is written through the writer's ``(Command)`` call form instead.
    """
    payload = command.payload
    name = str(command.name)

    if name == "setblock":
        extra = _state_kwargs(payload.get("state") or {})
        return f"setblock({_literal(payload['pos'])}, {_literal(payload['block'])}{extra})"
    if name == "fill":
        extra = _state_kwargs(payload.get("state") or {})
        mode = f", mode={payload['mode']!r}" if payload.get("mode") else ""
        return (
            f"fill({_literal(payload['from'])}, {_literal(payload['to'])}, "
            f"{_literal(payload['block'])}{mode}{extra})"
        )
    if name == "say":
        return f"say({payload['text']!r})"
    if name == "tellraw":
        target = payload.get("target", "@a")
        extra = f", target={target!r}" if target != "@a" else ""
        return f"tellraw({payload['text']!r}{extra})"
    if name == "playsound":
        extra = ""
        if payload.get("source", "master") != "master":
            extra += f", source={payload['source']!r}"
        if payload.get("target", "@a") != "@a":
            extra += f", target={payload['target']!r}"
        return f"playsound({payload['sound']!r}{extra})"
    if name == "particle":
        return f"particle({payload['particle']!r}, {_literal(payload['pos'])})"
    if name == "place":
        extra = ""
        if payload.get("pos") is not None:
            extra += f", {_literal(payload['pos'])}"
        if payload.get("rotation") is not None:
            extra += f", rotation={payload['rotation']!r}"
        if payload.get("mirror") is not None:
            extra += f", mirror={payload['mirror']!r}"
        return f"place({_literal(payload['structure'])}{extra})"
    if name == "summon":
        pos = payload.get("pos")
        extra = f", {_literal(pos)}" if pos is not None else ""
        return f"summon({_literal(payload['entity'])}{extra})"
    if name == "give":
        extra = ""
        if payload.get("target", "@p") != "@p":
            extra += f", target={payload['target']!r}"
        if payload.get("count", 1) != 1:
            extra += f", count={payload['count']!r}"
        if payload.get("name") is not None:
            extra += f", name={payload['name']!r}"
        return f"give({_literal(payload['item'])}{extra})"
    if name == "scoreboard_set":
        return (
            f"set_score({payload['objective']!r}, {payload['entry']!r}, "
            f"{payload['value']!r})"
        )
    if name == "scoreboard_add":
        return (
            f"add_score({payload['objective']!r}, {payload['entry']!r}, "
            f"{payload['value']!r})"
        )
    return None


def _emit_effect(
    lines: list[str], receiver: str, command: Command, indent: int = 4
) -> None:
    """Append one effect line, unwrapping ``execute_if_score`` into ``if_score``."""
    pad = " " * indent
    if command.name == "execute_if_score":
        inner = command.payload.get("run")
        if isinstance(inner, Command):
            payload = command.payload
            guard = (
                f"if_score({payload['objective']!r}, {payload['entry']!r}, "
                f"{payload['value']!r})"
            )
            call = _effect_call(inner)
            if call is not None:
                lines.append(f"{pad}{receiver}.{guard}.{call}")
                return
            lines.append(f"{pad}{receiver}({_command_literal(command)})")
            return

    call = _effect_call(command)
    if call is not None:
        lines.append(f"{pad}{receiver}.{call}")
    else:
        # No writer method models this one — pass the Command through verbatim.
        lines.append(f"{pad}{receiver}({_command_literal(command)})")


def _guard_key(command: Command) -> tuple[Any, Any, Any] | None:
    """The ``(objective, entry, value)`` a guarded effect shares, else ``None``.

    Only effects the writer can express are groupable — one that has to fall
    back to a literal ``Command`` carries its own guard inside it.
    """
    if command.name != "execute_if_score":
        return None
    inner = command.payload.get("run")
    if not isinstance(inner, Command) or _effect_call(inner) is None:
        return None
    payload = command.payload
    return (payload["objective"], payload["entry"], payload["value"])


def _emit_effects(
    lines: list[str], receiver: str, commands: Sequence[Command], indent: int
) -> None:
    """Emit a phase's effects, grouping consecutive identical guards into a block.

    A run of two or more effects sharing one ``if_score`` guard becomes a
    ``with`` block, so the condition is written once — matching how the same
    machine would be written by hand. A lone guarded effect stays a chained
    one-liner, which reads better than a one-line block.
    """
    position = 0
    while position < len(commands):
        key = _guard_key(commands[position])
        run_end = position + 1
        if key is not None:
            while run_end < len(commands) and _guard_key(commands[run_end]) == key:
                run_end += 1

        if key is not None and run_end - position > 1:
            objective, entry, value = key
            pad = " " * indent
            variable = "guarded" if not receiver.endswith(".do") else "guarded_do"
            lines.append(
                f"{pad}with {receiver}.if_score({objective!r}, {entry!r}, "
                f"{value!r}) as {variable}:"
            )
            for command in commands[position:run_end]:
                inner = command.payload["run"]
                lines.append(f"{pad}    {variable}.{_effect_call(inner)}")
        else:
            for command in commands[position:run_end]:
                _emit_effect(lines, receiver, command, indent)
        position = run_end


def _needs_command_import(machines: list[Machine[Any]]) -> bool:
    """Whether any effect falls back to a literal ``Command(...)``."""

    def unmodelled(command: Command) -> bool:
        if command.name == "execute_if_score":
            inner = command.payload.get("run")
            return not isinstance(inner, Command) or _effect_call(inner) is None
        return _effect_call(command) is None

    for machine in machines:
        for state in machine.states.values():
            if any(unmodelled(c) for c in (*state.enter, *state.exit, *state.cycle)):
                return True
        if any(unmodelled(c) for t in machine.transitions for c in t.commands):
            return True
    return False


def _needs_blockpos(machines: list[Machine[Any]]) -> bool:
    """Whether any payload carries a :class:`BlockPos` literal."""

    def scan(command: Command) -> bool:
        for value in command.payload.values():
            if isinstance(value, BlockPos):
                return True
            if isinstance(value, Command) and scan(value):
                return True
        return False

    for machine in machines:
        for state in machine.states.values():
            if any(scan(c) for c in (*state.enter, *state.exit, *state.cycle)):
                return True
        if any(scan(c) for t in machine.transitions for c in t.commands):
            return True
    return False


def _emit_machine(machine: Machine[Any], lines: list[str]) -> str:
    """Emit one ``build_<name>()`` function; return its name."""
    used: set[str] = {"builder"}
    variables = {
        name: _identifier(name, used=used) for name in machine.states
    }
    function_name = f"build_{_identifier(machine.name, used=set(), fallback='machine')}"

    lines.append(f"def {function_name}() -> MachineDefault:")
    lines.append(f'    """Rebuild the \'{machine.name}\' machine."""')
    lines.append(f"    builder = new_machine({machine.name!r})")
    if machine.entity is not None:
        lines.append(f"    builder.for_entity({machine.entity!r})")
    lines.append("")

    for name, state in machine.states.items():
        variable = variables[name]
        final = ", final=True" if state.is_final else ""
        phases = (
            ("enter", state.enter),
            ("exit", state.exit),
            ("cycle", state.cycle),
        )
        if any(commands for _, commands in phases):
            # A `with` block groups the state's definition, as in the handwritten
            # examples. The variable stays bound afterwards for the transitions.
            lines.append(f"    with builder.add_state({name!r}{final}) as {variable}:")
            for phase, commands in phases:
                _emit_effects(lines, f"{variable}.{phase}", commands, indent=8)
        else:
            # Nothing to group — a block would just need a `pass`.
            lines.append(f"    {variable} = builder.add_state({name!r}{final})")
        lines.append("")

    for position, transition in enumerate(machine.transitions):
        source = variables.get(transition.source, repr(transition.source))
        target = variables.get(transition.target, repr(transition.target))
        event = (
            "TICK_EVENT" if transition.event == TICK_EVENT else repr(transition.event)
        )
        if transition.condition is None and not transition.commands:
            lines.append(
                f"    builder.transition({source}, {event}, to={target})"
            )
            continue
        variable = f"edge_{position}"
        lines.append(
            f"    with builder.add_transition({source}, {event}, to={target}) "
            f"as {variable}:"
        )
        _emit_effects(lines, f"{variable}.do", transition.commands, indent=8)
        if transition.condition is not None:
            payload = transition.condition.payload
            lines.append(
                f"        {variable}.when_score({payload['objective']!r}, "
                f"{payload['entry']!r}, {payload['value']!r})"
            )

    lines.append("")
    lines.append(f"    builder.initial({variables[machine.initial]})")
    lines.append("    return builder.build()")
    lines.append("")
    lines.append("")
    return function_name


def generate_python(
    machines: list[Machine[Any]],
    *,
    namespace: str,
    description: str,
    version: str,
    flavor: str,
    origin: str,
) -> str:
    """Render ``machines`` as a runnable builder module.

    The generated file rebuilds the machines and recompiles them to the same
    target, so running it reproduces the datapack it was decompiled from.
    """
    uses_tick = any(
        transition.event == TICK_EVENT
        for machine in machines
        for transition in machine.transitions
    )

    header = [
        '"""Decompiled from the datapack ``' + origin + '``.',
        "",
        f"Reconstructed by **grimmcraft-decompile** for Minecraft {version}",
        f"({flavor}). Running this module recompiles an equivalent datapack:",
        "",
        "    uv run python <this file>",
        "",
        "State and event names come from the comments the compiler wrote into the",
        "pack; effects were read back out of the generated mcfunction lines.",
        '"""',
        "",
        "from grimmcraft_compiler import Target, compile_machines",
    ]
    control_imports = ["MachineDefault", "new_machine"]
    if uses_tick:
        control_imports.insert(0, "TICK_EVENT")
    if _needs_command_import(machines):
        control_imports.insert(0, "Command")
    header.append(
        "from grimmcraft_control import " + ", ".join(sorted(control_imports))
    )
    if _needs_blockpos(machines):
        header.append("from grimmcraft_core import BlockPos")
    header.extend(["", f"NAMESPACE = {namespace!r}", f"VERSION = {version!r}",
                   f"FLAVOR = {flavor!r}", f"DESCRIPTION = {description!r}", "", ""])

    lines: list[str] = list(header)
    built = [_emit_machine(machine, lines) for machine in machines]

    lines.append("def main() -> None:")
    lines.append('    """Rebuild every machine and compile them back to a datapack."""')
    lines.append(f"    machines = [{', '.join(f'{name}()' for name in built)}]")
    lines.append("    target = Target.resolve(VERSION, FLAVOR)")
    lines.append(
        "    compile_machines(machines, target, namespace=NAMESPACE, "
        "description=DESCRIPTION)"
    )
    lines.append("")
    lines.append("")
    lines.append('if __name__ == "__main__":')
    lines.append("    main()")

    return "\n".join(lines) + "\n"
