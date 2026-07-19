"""A tokenizer and parser for SNBT — Minecraft's stringified NBT.

Item data cannot be migrated with regular expressions.  ``{Enchantments:[{id:"…",
lvl:5s}]}`` nests, quotes may contain braces, and the transformation has to know
which brace closes which compound.  So this parses properly, and the classifier
pass — which only counts things — is the only place patterns are used.

The node types deliberately remember *how* a value was written: an integer that
appeared as ``1b`` keeps its ``b`` suffix, a string keeps the quote character it
used.  Two reasons:

* **Idempotency.** Re-serialising an untouched value has to reproduce it exactly,
  or running the migration twice would keep churning the file.
* **Type fidelity.** ``lvl:5s`` (short) and ``lvl:5`` (int) are different NBT
  types, and dropping the suffix silently changes the data.

Standard library only, so this module can be lifted out and run anywhere.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

#: Suffixes that mark a number's NBT type.
NUMERIC_SUFFIXES = "bBsSlLfFdD"

#: The prefixes that introduce a typed array: ``[I;1,2,3]``.
ARRAY_PREFIXES = {"B": "byte", "I": "int", "L": "long"}


class SnbtSyntaxError(ValueError):
    """SNBT that could not be parsed, with the offending position."""

    def __init__(self, message: str, text: str, position: int) -> None:
        self.text = text
        self.position = position
        excerpt = text[max(0, position - 30) : position + 30]
        super().__init__(
            f"{message} at position {position}\n  …{excerpt}…\n"
            f"  {' ' * (min(position, 30) + 3)}^"
        )


# --- the node types ----------------------------------------------------------


class SnbtValue:
    """Base class for every parsed SNBT value."""

    def to_snbt(self) -> str:
        """Serialise back to SNBT text."""
        raise NotImplementedError


@dataclass
class SnbtString(SnbtValue):
    """A string, remembering whether and how it was quoted."""

    value: str
    #: ``'"'``, ``"'"``, or ``""`` when the string was written bare.
    quote: str = '"'

    def to_snbt(self) -> str:
        if not self.quote:
            return self.value
        escaped = self.value.replace("\\", "\\\\").replace(self.quote, f"\\{self.quote}")
        return f"{self.quote}{escaped}{self.quote}"


@dataclass
class SnbtNumber(SnbtValue):
    """A number, keeping the exact text and type suffix it was written with."""

    text: str
    suffix: str = ""

    def to_snbt(self) -> str:
        return f"{self.text}{self.suffix}"

    def as_int(self) -> int:
        return int(float(self.text))

    def as_float(self) -> float:
        return float(self.text)


@dataclass
class SnbtBoolean(SnbtValue):
    """``true`` / ``false`` — stored by the game as a byte."""

    value: bool

    def to_snbt(self) -> str:
        return "true" if self.value else "false"


@dataclass
class SnbtList(SnbtValue):
    """An untyped list: ``[a,b,c]``."""

    items: list[SnbtValue] = field(default_factory=list)

    def to_snbt(self) -> str:
        return "[" + ",".join(item.to_snbt() for item in self.items) + "]"

    def __iter__(self) -> Any:
        return iter(self.items)

    def __len__(self) -> int:
        return len(self.items)


@dataclass
class SnbtArray(SnbtValue):
    """A typed array: ``[I;1,2,3]``, ``[B;1b]``, ``[L;1l]``."""

    prefix: str
    items: list[SnbtValue] = field(default_factory=list)

    def to_snbt(self) -> str:
        body = ",".join(item.to_snbt() for item in self.items)
        return f"[{self.prefix};{body}]"


@dataclass
class SnbtCompound(SnbtValue):
    """A compound: ``{key:value,…}``, preserving key order."""

    entries: dict[str, SnbtValue] = field(default_factory=dict)
    #: Keys that were quoted in the source, so they can be quoted again.
    quoted_keys: set[str] = field(default_factory=set)

    def to_snbt(self) -> str:
        parts = []
        for key, value in self.entries.items():
            name = f'"{key}"' if key in self.quoted_keys else key
            parts.append(f"{name}:{value.to_snbt()}")
        return "{" + ",".join(parts) + "}"

    # Convenience accessors so rules read naturally.
    def __contains__(self, key: object) -> bool:
        return key in self.entries

    def __getitem__(self, key: str) -> SnbtValue:
        return self.entries[key]

    def __setitem__(self, key: str, value: SnbtValue) -> None:
        self.entries[key] = value

    def get(self, key: str, default: SnbtValue | None = None) -> SnbtValue | None:
        return self.entries.get(key, default)

    def pop(self, key: str, default: SnbtValue | None = None) -> SnbtValue | None:
        return self.entries.pop(key, default)

    def keys(self) -> Any:
        return self.entries.keys()

    def items(self) -> Any:
        return self.entries.items()

    def __len__(self) -> int:
        return len(self.entries)


# --- the parser --------------------------------------------------------------


class SnbtParser:
    """A recursive-descent parser over one SNBT string."""

    def __init__(self, text: str) -> None:
        self.text = text
        self.position = 0

    # --- cursor helpers ------------------------------------------------------
    def peek(self) -> str:
        return self.text[self.position] if self.position < len(self.text) else ""

    def skip_whitespace(self) -> None:
        while self.position < len(self.text) and self.text[self.position] in " \t\n\r":
            self.position += 1

    def expect(self, character: str) -> None:
        self.skip_whitespace()
        if self.peek() != character:
            raise SnbtSyntaxError(
                f"expected {character!r} but found {self.peek()!r}",
                self.text,
                self.position,
            )
        self.position += 1

    # --- values --------------------------------------------------------------
    def parse(self) -> SnbtValue:
        """Parse the whole string, rejecting anything left over."""
        value = self.parse_value()
        self.skip_whitespace()
        if self.position != len(self.text):
            raise SnbtSyntaxError("unexpected trailing text", self.text, self.position)
        return value

    def parse_value(self) -> SnbtValue:
        self.skip_whitespace()
        character = self.peek()
        if not character:
            raise SnbtSyntaxError("unexpected end of input", self.text, self.position)
        if character == "{":
            return self.parse_compound()
        if character == "[":
            return self.parse_list_or_array()
        if character in "\"'":
            return self.parse_quoted_string()
        return self.parse_bare_value()

    def parse_compound(self) -> SnbtCompound:
        self.expect("{")
        compound = SnbtCompound()
        self.skip_whitespace()
        if self.peek() == "}":
            self.position += 1
            return compound

        while True:
            self.skip_whitespace()
            if self.peek() in "\"'":
                key_node = self.parse_quoted_string()
                key = key_node.value
                compound.quoted_keys.add(key)
            else:
                key = self.parse_bare_key()
            self.expect(":")
            compound.entries[key] = self.parse_value()
            self.skip_whitespace()
            if self.peek() == ",":
                self.position += 1
                continue
            self.expect("}")
            return compound

    def parse_list_or_array(self) -> SnbtValue:
        self.expect("[")
        # A typed array is '[X;' — look ahead two characters to tell them apart.
        if (
            self.position + 1 < len(self.text)
            and self.text[self.position] in ARRAY_PREFIXES
            and self.text[self.position + 1] == ";"
        ):
            prefix = self.text[self.position]
            self.position += 2
            array = SnbtArray(prefix)
            self.skip_whitespace()
            if self.peek() == "]":
                self.position += 1
                return array
            while True:
                array.items.append(self.parse_value())
                self.skip_whitespace()
                if self.peek() == ",":
                    self.position += 1
                    continue
                self.expect("]")
                return array

        listing = SnbtList()
        self.skip_whitespace()
        if self.peek() == "]":
            self.position += 1
            return listing
        while True:
            listing.items.append(self.parse_value())
            self.skip_whitespace()
            if self.peek() == ",":
                self.position += 1
                continue
            self.expect("]")
            return listing

    def parse_quoted_string(self) -> SnbtString:
        quote = self.peek()
        self.position += 1
        characters: list[str] = []
        while True:
            if self.position >= len(self.text):
                raise SnbtSyntaxError("unterminated string", self.text, self.position)
            character = self.text[self.position]
            if character == "\\":
                self.position += 1
                if self.position >= len(self.text):
                    raise SnbtSyntaxError(
                        "unterminated escape", self.text, self.position
                    )
                characters.append(self.text[self.position])
                self.position += 1
                continue
            if character == quote:
                self.position += 1
                return SnbtString("".join(characters), quote)
            characters.append(character)
            self.position += 1

    def parse_bare_key(self) -> str:
        start = self.position
        while self.position < len(self.text) and (
            self.text[self.position].isalnum()
            or self.text[self.position] in "_-.+"
        ):
            self.position += 1
        if start == self.position:
            raise SnbtSyntaxError("expected a key", self.text, self.position)
        return self.text[start:self.position]

    def parse_bare_value(self) -> SnbtValue:
        """A number, boolean, or unquoted string."""
        start = self.position
        while self.position < len(self.text) and self.text[self.position] not in ",{}[]:":
            self.position += 1
        raw = self.text[start:self.position].strip()
        if not raw:
            raise SnbtSyntaxError("expected a value", self.text, start)

        if raw == "true":
            return SnbtBoolean(True)
        if raw == "false":
            return SnbtBoolean(False)

        # A number optionally ends in a type suffix (1b, 2s, 3L, 4.5f).
        body, suffix = raw, ""
        if len(raw) > 1 and raw[-1] in NUMERIC_SUFFIXES:
            body, suffix = raw[:-1], raw[-1]
        if _looks_numeric(body):
            return SnbtNumber(body, suffix)
        return SnbtString(raw, "")


def _looks_numeric(text: str) -> bool:
    if not text or text in ("-", "+", "."):
        return False
    try:
        float(text)
    except ValueError:
        return False
    return True


def parse_snbt(text: str) -> SnbtValue:
    """Parse an SNBT string into nodes, raising :class:`SnbtSyntaxError`."""
    return SnbtParser(text).parse()


def parse_compound(text: str) -> SnbtCompound:
    """Parse SNBT that must be a compound, e.g. an item's ``{…}`` tag."""
    value = parse_snbt(text)
    if not isinstance(value, SnbtCompound):
        raise SnbtSyntaxError(
            f"expected a compound but found {type(value).__name__}", text, 0
        )
    return value


def find_matching_brace(text: str, start: int) -> int:
    """The index just past the brace/bracket group opening at ``start``.

    Quote-aware, so a ``}`` inside a string does not end the group. Used to cut
    an item's data out of a command line before parsing it.
    """
    opener = text[start]
    closer = {"{": "}", "[": "]"}.get(opener)
    if closer is None:
        raise SnbtSyntaxError("not an opening brace", text, start)

    depth = 0
    position = start
    quote = ""
    while position < len(text):
        character = text[position]
        if quote:
            if character == "\\":
                position += 2
                continue
            if character == quote:
                quote = ""
        elif character in "\"'":
            quote = character
        elif character in "{[":
            depth += 1
        elif character in "}]":
            depth -= 1
            if depth == 0:
                return position + 1
        position += 1
    raise SnbtSyntaxError("unbalanced braces", text, start)
