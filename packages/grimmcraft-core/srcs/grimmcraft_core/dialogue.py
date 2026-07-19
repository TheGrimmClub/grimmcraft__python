"""Branching NPC dialogue, modelled the way Ren'Py models a script.

A dialogue is a set of named **scenes**. A scene says some lines, runs some
effects, and then either falls through to another scene or offers the player a
**menu** of options, each leading somewhere. That is exactly a Ren'Py ``label``
with its ``say`` statements and ``menu`` block::

    label start:                         with talk.scene("start") as start:
        e "Welcome."                         start.say("Welcome.")
        menu:                                with start.menu() as choices:
            "Who are you?":                      choices.option("Who are you?",
                jump about                                      goto="about")

Which is also, exactly, a **state machine**: scenes are states, options are
transitions, and the option a player picks is the event. So a dialogue lowers to
a :class:`~grimmcraft_control.machine.Machine` and inherits the whole existing
pipeline — validation, compilation, the round-trip guarantee, and decompilation
back to readable Python.

This module is the *data model* only: pure, immutable, and free of any Minecraft
syntax. The builder that constructs it and the lowering that turns it into a
machine live in ``grimmcraft-npc``, because both need command constructors from
``grimmcraft-control`` — which depends on this package, so this package cannot
depend on it.
"""

# Includes
from __future__ import annotations

from grimmclub_standardlib import dataclass, field, replace
from grimmcraft_core.protocols import CommandLike
from grimmcraft_core.text import Text, as_text


# Functions
#: The event name of the *n*-th option out of a scene. Options are identified
#: positionally because a label is prose — it may be changed, translated or
#: repeated — while its position in the menu is stable.
def option_event(index: int) -> str:
    """The machine event fired when the player picks option ``index``."""
    return f"choice_{index}"

# Classes
@dataclass(frozen=True, slots=True)
class Condition:
    """A score check gating an option — the compilable form of Ren'Py's ``if``.

    Mirrors ``grimmcraft_control.Condition``'s ``score_matches`` payload, kept
    here as its own type so the dialogue model stays independent of control.
    """

    objective: str
    entry: str
    value: int


@dataclass(frozen=True, slots=True)
class Option:
    """One choice in a menu: what it reads as, and where it leads."""

    label: Text
    goto: str
    #: Only offered when this holds. ``None`` means always available.
    condition: Condition | None = None
    #: Effects run when this option is picked (before entering ``goto``).
    effects: tuple[CommandLike, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "label", as_text(self.label))


@dataclass(frozen=True, slots=True)
class Scene:
    """One node of the dialogue: lines to say, effects to run, and where next.

    A scene ends in exactly one of three ways, checked by :meth:`validate`:

    * ``options`` — the player is asked to choose (a Ren'Py ``menu``);
    * ``goto`` — it falls straight through to another scene (a ``jump``);
    * ``is_end`` — the conversation closes.
    """

    name: str
    lines: tuple[Text, ...] = ()
    effects: tuple[CommandLike, ...] = ()
    options: tuple[Option, ...] = ()
    goto: str | None = None
    is_end: bool = False

    @property
    def is_menu(self) -> bool:
        """True when this scene asks the player to pick an option."""
        return bool(self.options)

    def targets(self) -> tuple[str, ...]:
        """Every scene this one can lead to."""
        if self.options:
            return tuple(option.goto for option in self.options)
        return (self.goto,) if self.goto else ()

    def validate(self) -> str | None:
        """Why this scene is malformed, or ``None`` when it is fine."""
        endings = sum((bool(self.options), self.goto is not None, self.is_end))
        if endings == 0:
            return (
                f"scene '{self.name}' neither offers options, nor goes to another "
                "scene, nor ends — the conversation would hang"
            )
        if endings > 1:
            return (
                f"scene '{self.name}' has more than one ending (options / goto / "
                "end); a scene may only finish one way"
            )
        return None


@dataclass(frozen=True, slots=True)
class Dialogue:
    """A whole conversation: named scenes plus the one they start from."""

    name: str
    #: Who is speaking — shown as the dialog screen's title.
    speaker: str | None = None
    scenes: dict[str, Scene] = field(default_factory=dict)
    start: str = "start"

    def __iter__(self):  # type: ignore[no-untyped-def]
        """Iterate scenes in declaration order — the order they were added."""
        return iter(self.scenes.values())

    def __len__(self) -> int:
        return len(self.scenes)

    def scene(self, name: str) -> Scene:
        """Look up a scene by name, raising ``KeyError`` if it is absent."""
        return self.scenes[name]

    def problems(self) -> list[str]:
        """Every structural problem with this dialogue, as readable sentences.

        Checked here rather than at build time so a caller can surface them as
        diagnostics instead of an exception.
        """
        found: list[str] = []
        if self.start not in self.scenes:
            found.append(
                f"dialogue '{self.name}' starts at '{self.start}', which is not a scene"
            )
        for scene in self.scenes.values():
            problem = scene.validate()
            if problem is not None:
                found.append(problem)
            for target in scene.targets():
                if target not in self.scenes:
                    found.append(
                        f"scene '{scene.name}' leads to '{target}', which is not a scene"
                    )
        return found

    def unreachable(self) -> list[str]:
        """Scenes no path from :attr:`start` can reach — usually a typo."""
        seen: set[str] = set()
        queue = [self.start] if self.start in self.scenes else []
        while queue:
            name = queue.pop()
            if name in seen:
                continue
            seen.add(name)
            queue.extend(
                target
                for target in self.scenes[name].targets()
                if target in self.scenes
            )
        return [name for name in self.scenes if name not in seen]

    def with_scene(self, scene: Scene) -> Dialogue:
        """A copy with ``scene`` added or replaced."""
        return replace(self, scenes={**self.scenes, scene.name: scene})
