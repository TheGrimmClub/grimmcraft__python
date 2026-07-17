"""The :class:`Dialect` — version-correct rendering of IR commands to text.

All version-specific command syntax lives here, resolved from the
:class:`~.target.Target`: item/block data as **components** (1.20.5+) vs **NBT
tags** (earlier), and text components as **SNBT** (1.21.5+) vs **JSON**.  Nothing
else in the compiler renders command text, so a version quirk is fixed in exactly
one place.
"""

from __future__ import annotations

import json
from typing import Any

from grimmcraft_compiler.target import Target
from grimmcraft_compiler.version import VersionTuple
from grimmcraft_control.machine import Command

#: First version whose text components are written as SNBT rather than JSON.
SNBT_TEXT_SINCE: VersionTuple = (1, 21, 5)


def id_string(value: Any) -> str:
    """The namespaced id of ``value`` — an enum member's ``.string_id`` or a str."""
    string_id = getattr(value, "string_id", None)
    if string_id is not None:
        return str(string_id)
    return str(value)


def _fmt_coord(n: Any) -> str:
    """Render one position axis: ints bare, floats trimmed of trailing zeros."""
    if isinstance(n, bool):  # avoid True/False slipping through as ints
        raise TypeError("coordinate cannot be a bool")
    if isinstance(n, int):
        return str(n)
    if isinstance(n, float):
        return format(n, "g")
    return str(n)


def position(value: Any) -> str:
    """Render a position: a ``BlockPos``/``Coordinates``, an ``(x, y, z)`` tuple,
    or a raw string like ``"~ ~1 ~"``."""
    if isinstance(value, str):
        return value
    if hasattr(value, "x") and hasattr(value, "y") and hasattr(value, "z"):
        return f"{_fmt_coord(value.x)} {_fmt_coord(value.y)} {_fmt_coord(value.z)}"
    if isinstance(value, (tuple, list)) and len(value) == 3:
        return " ".join(_fmt_coord(n) for n in value)
    raise TypeError(f"cannot render position from {value!r}")


class Dialect:
    """Renders :class:`Command`\\ s for one :class:`Target`."""

    def __init__(self, target: Target) -> None:
        self.target = target
        self.info = target.info

    # --- text components -----------------------------------------------------
    def text_component(self, text: str) -> str:
        """A ``{"text": ...}`` component as JSON or SNBT per target version."""
        if self.info.version_tuple >= SNBT_TEXT_SINCE:
            # SNBT: unquoted keys, double-quoted string values.
            escaped = text.replace("\\", "\\\\").replace('"', '\\"')
            return f'{{text:"{escaped}"}}'
        return json.dumps({"text": text}, separators=(",", ":"))

    # --- items ---------------------------------------------------------------
    def item_with_name(self, item_id: str, name: str | None) -> str:
        """Render an item id, optionally with a custom name, per data model.

        Components (1.20.5+): ``item[minecraft:custom_name=<text>]``.
        NBT (earlier): ``item{display:{Name:'<json text>'}}``.
        """
        if name is None:
            return item_id
        if self.info.uses_components:
            return f"{item_id}[minecraft:custom_name={self.text_component(name)}]"
        json_text = json.dumps({"text": name}, separators=(",", ":"))
        return f"{item_id}{{display:{{Name:'{json_text}'}}}}"

    # --- block states --------------------------------------------------------
    def block_with_state(self, block_id: str, state: dict[str, Any] | None) -> str:
        """Render a block id with an optional ``[prop=value,...]`` state palette."""
        if not state:
            return block_id
        props = ",".join(f"{k}={v}" for k, v in state.items())
        return f"{block_id}[{props}]"

    # --- dispatch ------------------------------------------------------------
    def render(self, command: Command) -> str:
        """Render one command to a single line of ``mcfunction`` text."""
        handler = getattr(self, f"_r_{command.name}", None)
        if handler is None:
            raise ValueError(f"dialect cannot render command {command.name!r}")
        rendered: str = handler(command.payload)
        return rendered

    # --- domain commands -----------------------------------------------------
    def _r_say(self, p: dict[str, Any]) -> str:
        return f"say {p['text']}"

    def _r_tellraw(self, p: dict[str, Any]) -> str:
        target = p.get("target", "@a")
        return f"tellraw {target} {self.text_component(p['text'])}"

    def _r_setblock(self, p: dict[str, Any]) -> str:
        block = self.block_with_state(id_string(p["block"]), p.get("state"))
        return f"setblock {position(p['pos'])} {block}"

    def _r_summon(self, p: dict[str, Any]) -> str:
        pos = position(p["pos"]) if "pos" in p else "~ ~ ~"
        return f"summon {id_string(p['entity'])} {pos}"

    def _r_give(self, p: dict[str, Any]) -> str:
        target = p.get("target", "@p")
        item = self.item_with_name(id_string(p["item"]), p.get("name"))
        count = p.get("count", 1)
        return f"give {target} {item} {count}"

    def _r_playsound(self, p: dict[str, Any]) -> str:
        source = p.get("source", "master")
        target = p.get("target", "@a")
        return f"playsound {p['sound']} {source} {target}"

    def _r_particle(self, p: dict[str, Any]) -> str:
        pos = position(p["pos"]) if "pos" in p else "~ ~ ~"
        return f"particle {id_string(p['particle'])} {pos}"

    def _r_raw(self, p: dict[str, Any]) -> str:
        return str(p["text"])

    # --- internal commands ---------------------------------------------------
    def _r_call(self, p: dict[str, Any]) -> str:
        return f"function {p['ref']}"

    def _r_comment(self, p: dict[str, Any]) -> str:
        return f"# {p['text']}"

    def _r_scoreboard_objective_add(self, p: dict[str, Any]) -> str:
        return (
            f"scoreboard objectives add {p['objective']} "
            f"{p.get('criterion', 'dummy')}"
        )

    def _r_scoreboard_set(self, p: dict[str, Any]) -> str:
        return f"scoreboard players set {p['entry']} {p['objective']} {p['value']}"

    def _r_scoreboard_add(self, p: dict[str, Any]) -> str:
        return f"scoreboard players add {p['entry']} {p['objective']} {p['value']}"

    def _r_execute_if_score(self, p: dict[str, Any]) -> str:
        inner = self.render(p["run"])
        return (
            f"execute if score {p['entry']} {p['objective']} "
            f"matches {p['value']} run {inner}"
        )
