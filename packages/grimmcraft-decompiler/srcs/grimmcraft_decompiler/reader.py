"""The :class:`CommandReader` — one ``mcfunction`` line back into a ``Command``.

This is the mirror of :class:`~grimmcraft_compiler.dialect.Dialect`: every
``_r_<name>`` renderer there has a ``_read_<verb>`` parser here, and the pair is
required to satisfy ``render(read(line)) == line`` for any line the compiler can
produce.  That identity is what the round-trip guarantee rests on, so a parser
that cannot reproduce a line **must** decline rather than guess.

Declining is safe: an unrecognised line becomes a ``raw`` command holding the
text verbatim, which the dialect renders straight back out.  That is why a
hand-written pack full of commands the IR has no model for (``summon`` with a big
NBT payload, ``scoreboard objectives setdisplay``, …) still round-trips at level
1 — nothing is ever dropped, it is only left unstructured.
"""

from __future__ import annotations

import json
import re
from typing import Any

from grimmcraft_compiler.dialect import Dialect
from grimmcraft_compiler.target import Target
from grimmcraft_compiler.version import COMPONENTS_SINCE
from grimmcraft_control.machine import Command, CommandName
from grimmcraft_core import BlockPos
from grimmcraft_decompiler.diagnostics import Codes, DiagnosticBag

#: ``execute if score <entry> <objective> matches <value> run <inner>``.
_EXECUTE_IF_SCORE = re.compile(
    r"^execute if score (?P<entry>\S+) (?P<objective>\S+) "
    r"matches (?P<value>-?\d+) run (?P<inner>.+)$"
)

#: ``scoreboard players set|add <entry> <objective> <value>``.
_SCOREBOARD_PLAYERS = re.compile(
    r"^scoreboard players (?P<verb>set|add) (?P<entry>\S+) (?P<objective>\S+) "
    r"(?P<value>-?\d+)$"
)

#: ``scoreboard objectives add <objective> <criterion>``.
_SCOREBOARD_OBJECTIVE = re.compile(
    r"^scoreboard objectives add (?P<objective>\S+) (?P<criterion>\S+)$"
)

#: ``<id>[prop=value,...]`` — a block id with an optional state palette.
_BLOCK_STATE = re.compile(r"^(?P<id>[^\[\]{}]+)\[(?P<props>[^\[\]]*)\]$")

#: SNBT text component: ``{text:"…"}`` (1.21.5+).
_SNBT_TEXT = re.compile(r'^\{text:"(?P<text>(?:[^"\\]|\\.)*)"\}$')

#: The NBT item-name shape the dialect writes before 1.20.5.
_NBT_ITEM_NAME = re.compile(
    r"^(?P<id>[^\[\]{}]+)\{display:\{Name:'(?P<json>.*)'\}\}$"
)

#: The components item-name shape the dialect writes from 1.20.5.
_COMPONENT_ITEM_NAME = re.compile(
    r"^(?P<id>[^\[\]{}]+)\[minecraft:custom_name=(?P<component>.+)\]$"
)


def _is_canonical_int(token: str) -> bool:
    """Whether ``token`` survives an ``int`` round-trip unchanged.

    ``"07"`` and ``"+7"`` are *not* canonical: re-rendering them as ``7`` would
    silently rewrite the pack, so they are kept as raw text instead.
    """
    try:
        return str(int(token)) == token
    except ValueError:
        return False


def parse_position(tokens: list[str]) -> Any:
    """Lift three coordinate tokens to a :class:`BlockPos`, or keep them as text.

    Only plain integers become a ``BlockPos``; relative (``~``), local (``^``) and
    decimal coordinates stay a string so the dialect echoes them back byte for
    byte (``format(1.50, "g")`` would emit ``1.5``).
    """
    if len(tokens) == 3 and all(_is_canonical_int(t) for t in tokens):
        return BlockPos(int(tokens[0]), int(tokens[1]), int(tokens[2]))
    return " ".join(tokens)


def parse_block(spec: str) -> tuple[str, dict[str, str] | None]:
    """Split ``minecraft:light[level=15]`` into its id and state mapping."""
    match = _BLOCK_STATE.match(spec)
    if match is None:
        return spec, None
    props = match.group("props")
    if not props:
        return match.group("id"), None
    state: dict[str, str] = {}
    for pair in props.split(","):
        key, sep, value = pair.partition("=")
        if not sep:
            return spec, None  # not a state palette after all — keep it whole
        state[key] = value
    return match.group("id"), state


def parse_text_component(raw: str) -> str | None:
    """Recover the plain text from a ``{"text": …}`` / ``{text:"…"}`` component.

    Returns ``None`` for anything richer (a JSON array, extra keys like
    ``color``, …) — the IR models only plain text, so a richer component has to
    stay raw rather than be silently flattened.
    """
    snbt = _SNBT_TEXT.match(raw)
    if snbt is not None:
        return snbt.group("text").replace('\\"', '"').replace("\\\\", "\\")
    try:
        document = json.loads(raw)
    except json.JSONDecodeError:
        return None
    if isinstance(document, dict) and set(document) == {"text"}:
        text = document["text"]
        return text if isinstance(text, str) else None
    return None


class CommandReader:
    """Parses ``mcfunction`` lines into IR :class:`Command`\\ s for one version.

    ``version`` selects which item-data model is *expected* (components from
    1.20.5, NBT before); both are always accepted, but reading the unexpected one
    raises ``GD2005`` because it means the pack and its ``pack_format`` disagree.
    """

    def __init__(self, target: Target, bag: DiagnosticBag) -> None:
        self.target = target
        self.version = target.info.version_tuple
        self.bag = bag
        self.uses_components = self.version >= COMPONENTS_SINCE
        # The very renderer the result will be checked against — reusing it (as
        # opposed to re-deriving the rules) is what keeps the two in lockstep.
        self.dialect = Dialect(target)

    # --- entry point ---------------------------------------------------------
    def read(self, line: str, *, source: str) -> Command:
        """Parse one line into a :class:`Command`, never raising.

        Every parse is **verified**: the candidate command is rendered back
        through the :class:`Dialect` and accepted only if it reproduces ``line``
        byte for byte.  Anything else degrades to ``raw``, which re-emits
        verbatim.  That inverts the usual burden of proof — a parser cannot
        silently normalise a pack (dropping a trailing space, reformatting a
        banner comment, rewriting ``07`` as ``7``), because the check would
        catch it and fall back.
        """
        if not line.strip():
            # A blank line is meaningful: it must survive re-rendering.
            return Command(CommandName.RAW, {"text": line})

        command = self._parse(line.strip(), source=source)
        if command is not None and self._reproduces(command, line):
            return command

        if command is None:
            self.bag.emit(
                Codes.UNPARSEABLE_COMMAND,
                f"cannot model this command declaratively: {line.strip()[:80]}"
                + ("…" if len(line.strip()) > 80 else ""),
                hint="kept verbatim as a 'raw' command — it re-emits unchanged, "
                "but --emit machine/python cannot interpret it",
                source=source,
            )
        return Command(CommandName.RAW, {"text": line})

    def _parse(self, stripped: str, *, source: str) -> Command | None:
        """Parse a stripped line, without the reproduction check."""
        if stripped.startswith("#"):
            # The dialect renders a comment as exactly "# " + text; any other
            # shape (banner "### x ###", tight "#disabled") fails the check
            # below and stays raw.
            return Command("comment", {"text": stripped[2:]}) if (
                stripped.startswith("# ")
            ) else None
        return self._dispatch(stripped, source=source)

    def _reproduces(self, command: Command, line: str) -> bool:
        """Whether rendering ``command`` yields ``line`` exactly."""
        try:
            return self.dialect.render(command) == line
        except (ValueError, KeyError, TypeError):
            return False

    def _dispatch(self, line: str, *, source: str) -> Command | None:
        """Try each parser; ``None`` means "no parser claimed this line"."""
        verb, _, rest = line.partition(" ")
        handler = getattr(self, f"_read_{verb}", None)
        if handler is None:
            return None
        parsed: Command | None = handler(rest, source)
        return parsed

    # --- domain commands -----------------------------------------------------
    def _read_say(self, rest: str, source: str) -> Command | None:
        return Command(CommandName.SAY, {"text": rest}) if rest else None

    def _read_tellraw(self, rest: str, source: str) -> Command | None:
        target, _, component = rest.partition(" ")
        if not component:
            return None
        text = parse_text_component(component)
        if text is None:
            return None  # a rich component — keep the line raw
        return Command(CommandName.TELLRAW, {"target": target, "text": text})

    def _read_setblock(self, rest: str, source: str) -> Command | None:
        tokens = rest.split()
        if len(tokens) != 4:
            return None
        block, state = parse_block(tokens[3])
        payload: dict[str, Any] = {"pos": parse_position(tokens[:3]), "block": block}
        if state:
            payload["state"] = state
        return Command(CommandName.SETBLOCK, payload)

    def _read_fill(self, rest: str, source: str) -> Command | None:
        tokens = rest.split()
        if len(tokens) not in (7, 8):
            return None
        block, state = parse_block(tokens[6])
        payload: dict[str, Any] = {
            "from": parse_position(tokens[:3]),
            "to": parse_position(tokens[3:6]),
            "block": block,
        }
        if state:
            payload["state"] = state
        if len(tokens) == 8:
            payload["mode"] = tokens[7]
        return Command(CommandName.FILL, payload)

    def _read_summon(self, rest: str, source: str) -> Command | None:
        tokens = rest.split()
        # Exactly "<entity> <x> <y> <z>" — an NBT payload is not modelled.
        if len(tokens) != 4:
            return None
        return Command(
            CommandName.SUMMON,
            {"entity": tokens[0], "pos": parse_position(tokens[1:4])},
        )

    def _read_give(self, rest: str, source: str) -> Command | None:
        target, _, remainder = rest.partition(" ")
        if not remainder:
            return None
        # The count is the final token; the item spec may contain spaces inside
        # its component/NBT braces, so split from the right.
        spec, _, count_text = remainder.rpartition(" ")
        if not spec or not _is_canonical_int(count_text):
            return None
        item, name = self._read_item(spec, source)
        if item is None:
            return None
        payload: dict[str, Any] = {
            "item": item,
            "target": target,
            "count": int(count_text),
        }
        if name is not None:
            payload["name"] = name
        return Command(CommandName.GIVE, payload)

    def _read_item(self, spec: str, source: str) -> tuple[str | None, str | None]:
        """Split an item spec into ``(id, custom_name)``; ``(None, None)`` if rich.

        Reports ``GD2005`` when the data model does not match the detected
        version — a components-style name on a pre-1.20.5 pack (or vice versa)
        means the version detection and the pack contents disagree.
        """
        if "[" not in spec and "{" not in spec:
            return spec, None

        components = _COMPONENT_ITEM_NAME.match(spec)
        if components is not None:
            name = parse_text_component(components.group("component"))
            if name is None:
                return None, None
            self._check_data_model(uses_components=True, source=source)
            return components.group("id"), name

        nbt = _NBT_ITEM_NAME.match(spec)
        if nbt is not None:
            try:
                document = json.loads(nbt.group("json"))
            except json.JSONDecodeError:
                return None, None
            if not isinstance(document, dict) or set(document) != {"text"}:
                return None, None
            self._check_data_model(uses_components=False, source=source)
            return nbt.group("id"), str(document["text"])

        return None, None

    def _check_data_model(self, *, uses_components: bool, source: str) -> None:
        if uses_components is self.uses_components:
            return
        found = "components" if uses_components else "NBT tags"
        expected = "components" if self.uses_components else "NBT tags"
        version = ".".join(str(part) for part in self.version)
        self.bag.emit(
            Codes.DATA_MODEL_MISMATCH,
            f"item data is written as {found}, but {version} expects {expected} "
            "(Minecraft moved item data from NBT tags to components in 1.20.5)",
            hint="pass --version to match the pack, or the re-emitted pack will "
            "use the detected version's model",
            source=source,
        )

    def _read_playsound(self, rest: str, source: str) -> Command | None:
        tokens = rest.split()
        if len(tokens) != 3:
            return None
        return Command(
            CommandName.PLAYSOUND,
            {"sound": tokens[0], "source": tokens[1], "target": tokens[2]},
        )

    def _read_dialog(self, rest: str, source: str) -> Command | None:
        """``dialog show <targets> <dialog>`` — the inverse of ``_r_dialog_show``.

        ``dialog clear`` carries no id and is not modelled, so it stays raw.
        """
        tokens = rest.split()
        if len(tokens) != 3 or tokens[0] != "show":
            return None
        return Command(
            CommandName.DIALOG_SHOW,
            {"dialog": tokens[2], "target": tokens[1], "min_version": "1.21.6"},
        )

    def _read_place(self, rest: str, source: str) -> Command | None:
        """``place template <id> <pos> [rotation [mirror]]`` — the inverse of
        :meth:`Dialect._r_place`.

        Only the ``template`` sub-command is modelled; ``place feature``,
        ``place jigsaw`` and friends stay raw.
        """
        tokens = rest.split()
        if len(tokens) < 5 or tokens[0] != "template":
            return None
        payload: dict[str, Any] = {
            "structure": tokens[1],
            "pos": parse_position(tokens[2:5]),
            "min_version": "1.19",
        }
        if len(tokens) >= 6:
            payload["rotation"] = tokens[5]
        if len(tokens) == 7:
            payload["mirror"] = tokens[6]
        if len(tokens) > 7:
            return None
        return Command(CommandName.PLACE, payload)

    def _read_particle(self, rest: str, source: str) -> Command | None:
        tokens = rest.split()
        if len(tokens) != 4:
            return None
        return Command(
            CommandName.PARTICLE,
            {"particle": tokens[0], "pos": parse_position(tokens[1:4])},
        )

    # --- internal commands ---------------------------------------------------
    def _read_function(self, rest: str, source: str) -> Command | None:
        return Command("call", {"ref": rest}) if rest and " " not in rest else None

    def _read_scoreboard(self, rest: str, source: str) -> Command | None:
        line = f"scoreboard {rest}"
        players = _SCOREBOARD_PLAYERS.match(line)
        if players is not None:
            name = (
                "scoreboard_set"
                if players.group("verb") == "set"
                else "scoreboard_add"
            )
            return Command(
                name,
                {
                    "objective": players.group("objective"),
                    "entry": players.group("entry"),
                    "value": int(players.group("value")),
                },
            )
        objective = _SCOREBOARD_OBJECTIVE.match(line)
        if objective is not None:
            return Command(
                "scoreboard_objective_add",
                {
                    "objective": objective.group("objective"),
                    "criterion": objective.group("criterion"),
                },
            )
        return None

    def _read_execute(self, rest: str, source: str) -> Command | None:
        """Parse ``execute if score … run <inner>``, recursing into the inner command.

        If the inner command is not itself modellable, the whole line is declined
        so it stays raw — a half-structured ``execute`` whose body is opaque
        would be a trap for the machine lifter.
        """
        match = _EXECUTE_IF_SCORE.match(f"execute {rest}")
        if match is None:
            return None
        inner = self._dispatch(match.group("inner").strip(), source=source)
        if inner is None:
            return None
        return Command(
            "execute_if_score",
            {
                "objective": match.group("objective"),
                "entry": match.group("entry"),
                "value": int(match.group("value")),
                "run": inner,
            },
        )
