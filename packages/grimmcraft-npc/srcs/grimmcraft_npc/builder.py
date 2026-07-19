"""The dialogue builder — a Ren'Py-shaped DSL over the core model.

Mirrors ``MachineBuilder``'s two styles and ``with``-block grouping, so a
dialogue reads the way the rest of the library does::

    talk = new_dialogue("miller", speaker="Marlene the Miller")

    with talk.scene("start") as start:
        start.say("Welcome to the mill, traveller.")
        with start.menu() as choices:
            choices.option("Who are you?", goto="about")
            choices.option("Goodbye.", goto="farewell")

Effects (``give``, ``set_flag``, …) go through the same
:class:`~grimmcraft_control.machine.writer.EffectWriter` every state and
transition uses, so anything expressible in a machine is expressible here.
"""

from __future__ import annotations

from typing import Any

from grimmcraft_control.machine import Command
from grimmcraft_control.machine.writer import EffectWriter
from grimmcraft_core.dialogue import (
    Condition,
    Dialogue,
    Option,
    Scene,
)
from grimmcraft_core.text import Text, as_text

#: The objective dialogue flags are stored in, mirroring ``grimmcraft_state``.
FLAG_OBJECTIVE = "grimmcraft_flag"


class OptionDraft:
    """One menu option under construction."""

    def __init__(self, label: Text, goto: str) -> None:
        self.label = label
        self.goto = goto
        self._condition: Condition | None = None
        self._effects: list[Command] = []

    def __enter__(self) -> OptionDraft:
        return self

    def __exit__(self, *exc: object) -> None:
        return None

    @property
    def do(self) -> EffectWriter:
        """Effects run when this option is picked."""
        return EffectWriter(self._effects)

    def when_score(self, objective: str, entry: str, value: int) -> OptionDraft:
        """Offer this option only when ``entry``'s ``objective`` score matches.

        The compilable form of Ren'Py's ``if`` inside a menu.
        """
        self._condition = Condition(objective, entry, value)
        return self

    def when_flag(self, flag: str, *, entry: str = "@s") -> OptionDraft:
        """Offer this option only once ``flag`` has been set."""
        return self.when_score(FLAG_OBJECTIVE, entry, _flag_value(flag))

    def to_option(self) -> Option:
        return Option(
            label=self.label,
            goto=self.goto,
            condition=self._condition,
            effects=tuple(self._effects),
        )


class MenuDraft:
    """A menu under construction — a list of options in the order declared."""

    def __init__(self) -> None:
        self.options: list[OptionDraft] = []

    def __enter__(self) -> MenuDraft:
        return self

    def __exit__(self, *exc: object) -> None:
        return None

    def option(self, label: Text | str, *, goto: str) -> OptionDraft:
        """Add a choice leading to the ``goto`` scene; returns it for chaining."""
        draft = OptionDraft(as_text(label), goto)
        self.options.append(draft)
        return draft


class SceneDraft:
    """A scene under construction: lines, effects, and one ending."""

    def __init__(self, name: str) -> None:
        self.name = name
        self._lines: list[Text] = []
        self._effects: list[Command] = []
        self._menu: MenuDraft | None = None
        self._goto: str | None = None
        self._end = False

    def __enter__(self) -> SceneDraft:
        return self

    def __exit__(self, *exc: object) -> None:
        return None

    # --- what the NPC says ---------------------------------------------------
    def say(self, text: Text | str, **style: Any) -> SceneDraft:
        """Add a spoken line. Style keywords build a :class:`Text` for you::

            scene.say("You look hungry.", color="gray", italic=True)
        """
        line = as_text(text)
        if style:
            line = line.styled(**style)
        self._lines.append(line)
        return self

    # --- what it does --------------------------------------------------------
    @property
    def do(self) -> EffectWriter:
        """Effects run when the scene is reached (``scene.do.give(...)``)."""
        return EffectWriter(self._effects)

    def give(self, item: Any, *, count: int = 1, target: str = "@s") -> SceneDraft:
        """Give the player an item — the common case, spelled directly."""
        self.do.give(item, count=count, target=target)
        return self

    def set_flag(self, flag: str, *, entry: str = "@s") -> SceneDraft:
        """Remember that something happened, for a later :meth:`when_flag`."""
        self.do.set_score(FLAG_OBJECTIVE, entry, _flag_value(flag))
        return self

    # --- how it ends ---------------------------------------------------------
    def menu(self) -> MenuDraft:
        """Ask the player to choose (Ren'Py's ``menu:``)."""
        self._menu = MenuDraft()
        return self._menu

    def goto(self, scene: str) -> SceneDraft:
        """Fall straight through to another scene (Ren'Py's ``jump``)."""
        self._goto = scene
        return self

    def end(self) -> SceneDraft:
        """Close the conversation here."""
        self._end = True
        return self

    def to_scene(self) -> Scene:
        return Scene(
            name=self.name,
            lines=tuple(self._lines),
            effects=tuple(self._effects),
            options=tuple(
                draft.to_option() for draft in (self._menu.options if self._menu else [])
            ),
            goto=self._goto,
            is_end=self._end,
        )


class DialogueBuilder:
    """Declares a :class:`Dialogue`, validated at :meth:`build`."""

    def __init__(self, name: str, *, speaker: str | None = None) -> None:
        self._name = name
        self._speaker = speaker
        self._scenes: list[SceneDraft] = []
        self._start: str | None = None

    def scene(self, name: str) -> SceneDraft:
        """Declare a scene and return it to fill in."""
        draft = SceneDraft(name)
        self._scenes.append(draft)
        return draft

    def starts_at(self, name: str) -> DialogueBuilder:
        """Choose the opening scene (defaults to the first one declared)."""
        self._start = name
        return self

    def build(self) -> Dialogue:
        """Freeze into an immutable :class:`Dialogue`.

        Raises :class:`ValueError` listing every structural problem at once —
        a dangling ``goto``, a scene with no ending — rather than one at a time.
        """
        if not self._scenes:
            raise ValueError(f"dialogue '{self._name}' has no scenes")

        scenes = {draft.name: draft.to_scene() for draft in self._scenes}
        dialogue = Dialogue(
            name=self._name,
            speaker=self._speaker,
            scenes=scenes,
            start=self._start or self._scenes[0].name,
        )
        problems = dialogue.problems()
        if problems:
            raise ValueError(
                f"dialogue '{self._name}' is not valid:\n  - "
                + "\n  - ".join(problems)
            )
        return dialogue


def new_dialogue(name: str, *, speaker: str | None = None) -> DialogueBuilder:
    """Start defining a dialogue called ``name`` — the friendly entry point."""
    return DialogueBuilder(name, speaker=speaker)


def _flag_value(flag: str) -> int:
    """A stable small integer for a named flag.

    Scoreboards hold ints, not names, so a flag needs a number. It is derived
    from the name so the same flag always maps to the same value across runs —
    ``hash()`` is salted per process and would not.
    """
    total = 0
    for char in flag:
        total = (total * 31 + ord(char)) % 2_000_000_000
    return total
