"""Rich text components — styled, clickable chat text.

Minecraft's *text component* is the JSON/SNBT structure behind ``tellraw``, item
names, dialog buttons and sign text.  This module models it as plain data;
rendering it to the version-correct syntax is the
:class:`~grimmcraft_compiler.dialect.Dialect`'s job, as with every other command.

A bare ``str`` remains perfectly valid everywhere a component is accepted — the
:class:`Text` class is only needed when something more than plain text is wanted:

    Text("Buy one.", color="green", click=run_command("village:miller/buy"))

Two version splits the renderer has to honour, both landing on **1.21.5**:

* the document syntax — JSON before, SNBT after;
* the event shape — ``clickEvent`` with a single ``value`` before,
  ``click_event`` with *action-specific* fields (``command``, ``url``) after.
"""

from __future__ import annotations

# Includes standard
from dataclasses import dataclass, field, replace

# Constants
#: Click actions a component may carry.
CLICK_ACTIONS = frozenset(
    {
        "run_command",
        "suggest_command",
        "open_url",
        "copy_to_clipboard",
        "change_page",
        # 1.21.6+: opens a dialog screen (see grimmcraft-structures' sibling docs).
        "show_dialog",
    }
)

#: The named colours Minecraft accepts (a ``#rrggbb`` hex string also works).
COLORS = frozenset(
    {
        "black", "dark_blue", "dark_green", "dark_aqua", "dark_red",
        "dark_purple", "gold", "gray", "dark_gray", "blue", "green",
        "aqua", "red", "light_purple", "yellow", "white",
    }
)

# Classes
@dataclass(frozen=True, slots=True)
class ClickEvent:
    """What happens when a player clicks this text.

    ``value`` carries the command / URL / page regardless of action; the
    renderer knows which field name each version and action wants, so callers
    never have to.
    """

    action: str
    value: str

    def __post_init__(self) -> None:
        if self.action not in CLICK_ACTIONS:
            allowed = ", ".join(sorted(CLICK_ACTIONS))
            raise ValueError(
                f"unknown click action {self.action!r}; choose one of: {allowed}"
            )

    @property
    def modern_field(self) -> str:
        """The action-specific field name used from 1.21.5."""
        if self.action in ("run_command", "suggest_command"):
            return "command"
        if self.action == "open_url":
            return "url"
        if self.action == "change_page":
            return "page"
        if self.action == "show_dialog":
            return "dialog"
        return "value"

@dataclass(frozen=True, slots=True)
class Text:
    """One styled text component, optionally with children.

    Every style field is tri-state: ``None`` means "inherit", which is what
    Minecraft does and what keeps the rendered document minimal — an unset field
    is simply not written.
    """

    text: str = ""
    color: str | None = None
    bold: bool | None = None
    italic: bool | None = None
    underlined: bool | None = None
    strikethrough: bool | None = None
    obfuscated: bool | None = None
    click: ClickEvent | None = None
    #: Tooltip shown on hover — plain text, the overwhelmingly common case.
    hover: str | None = None
    #: Appended components, which inherit this one's style.
    extra: tuple[Text, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if (
            self.color is not None
            and self.color not in COLORS
            and not _is_hex_color(self.color)
        ):
            raise ValueError(
                f"unknown colour {self.color!r}; use a named colour or '#rrggbb'"
            )

    @property
    def is_plain(self) -> bool:
        """True when this is nothing but text — no style, events or children.

        The renderer uses this to emit exactly what a bare ``str`` would, so
        adding rich text cannot change any existing pack's bytes.
        """
        return (
            self.color is None
            and self.bold is None
            and self.italic is None
            and self.underlined is None
            and self.strikethrough is None
            and self.obfuscated is None
            and self.click is None
            and self.hover is None
            and not self.extra
        )

    def styled(self, **changes: object) -> Text:
        """A copy with some fields replaced — ``line.styled(color="red")``."""
        return replace(self, **changes)  # type: ignore[arg-type]

    def then(self, *parts: Text | str) -> Text:
        """A copy with ``parts`` appended as children."""
        appended = tuple(
            part if isinstance(part, Text) else Text(part) for part in parts
        )
        return replace(self, extra=self.extra + appended)

    def __str__(self) -> str:
        """The plain text, children included — useful for logs and tests."""
        return self.text + "".join(str(child) for child in self.extra)


# Functions
def run_command(command: str) -> ClickEvent:
    """Click to run ``command`` (given without a leading ``/``)."""
    return ClickEvent("run_command", command.lstrip("/"))


def suggest_command(command: str) -> ClickEvent:
    """Click to put ``command`` in the player's chat box."""
    return ClickEvent("suggest_command", command.lstrip("/"))


def open_url(url: str) -> ClickEvent:
    """Click to open ``url``."""
    return ClickEvent("open_url", url)


def show_dialog(dialog: str) -> ClickEvent:
    """Click to open the ``ns:name`` dialog screen (1.21.6+)."""
    return ClickEvent("show_dialog", dialog)


def _is_hex_color(value: str) -> bool:
    return (
        len(value) == 7
        and value.startswith("#")
        and all(c in "0123456789abcdefABCDEF" for c in value[1:])
    )


def as_text(value: Text | str) -> Text:
    """Coerce a ``str`` to a plain :class:`Text` (a ``Text`` passes through)."""
    return value if isinstance(value, Text) else Text(value)
