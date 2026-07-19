"""Lower a :class:`Dialogue` to a :class:`Machine` — with two presentation backends.

A dialogue *is* a state machine, so almost all of this is a direct translation:
scenes become states, options become transitions, and the option a player picks
is the event.  What differs by target version is only how a scene is **shown**:

* **1.21.6+** — a vanilla ``dialog`` screen.  Each scene becomes a
  ``data/<ns>/dialog/<dialogue>/<scene>.json`` resource and the state's enter
  effects are a single ``dialog show @s <id>``.  Buttons carry the action, so
  the choice is a real UI element.
* **earlier** — clickable chat.  The lines become ``tellraw``, and each option
  becomes a ``tellraw`` whose ``clickEvent`` runs the dispatcher function.

Both drive the *same* machine, so the transitions, guards and effects — the
actual behaviour — are identical either way.  Only the presentation layer knows
which version it is targeting, which is the same split the rest of the compiler
uses.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from grimmcraft_compiler.ir import Resource, ResourceLocation
from grimmcraft_compiler.target import Target
from grimmcraft_compiler.version import VersionTuple
from grimmcraft_control.machine import (
    Command,
    Condition,
    ConditionName,
    Machine,
    MachineBuilder,
)
from grimmcraft_control.machine import effects as fx
from grimmcraft_core.entity.dialogue import Dialogue, Scene, option_event
from grimmcraft_core.text import Text, run_command

#: First version with the vanilla ``dialog`` registry (data/<ns>/dialog/*.json).
DIALOGS_SINCE: VersionTuple = (1, 21, 6)

#: The event a scene uses to fall through to the next one (Ren'Py's ``jump``).
CONTINUE_EVENT = "continue"

#: Label of the button that advances a non-menu scene.
CONTINUE_LABEL = "Continue"


@dataclass(slots=True)
class LoweredDialogue:
    """The result: a machine, plus the JSON resources it needs."""

    machine: Machine[Any]
    resources: list[Resource] = field(default_factory=list)
    #: Which backend was chosen, for reporting ("dialog" or "tellraw").
    backend: str = "dialog"

    @property
    def uses_dialog_screens(self) -> bool:
        return self.backend == "dialog"


def uses_dialog_screens(target: Target) -> bool:
    """Whether ``target`` can show native dialog screens (1.21.6+)."""
    return target.info.version_tuple >= DIALOGS_SINCE


class _DialogueLowering:
    """Lowers one dialogue for one target."""

    def __init__(self, dialogue: Dialogue, target: Target, namespace: str) -> None:
        self.dialogue = dialogue
        self.target = target
        self.ns = namespace
        self.native = uses_dialog_screens(target)
        self.resources: list[Resource] = []

    # --- ids -----------------------------------------------------------------
    def dispatcher(self, event: str) -> str:
        """The function a button/click runs to fire ``event`` on the machine.

        This mirrors ``lower.py``'s naming exactly — a dialogue is only useful
        if its buttons call the functions the machine lowering actually emits.
        """
        return f"{self.ns}:{self.dialogue.name}/on_{event}"

    def dialog_id(self, scene: Scene) -> ResourceLocation:
        return ResourceLocation(self.ns, f"{self.dialogue.name}/{scene.name}")

    # --- presentation --------------------------------------------------------
    def present(self, scene: Scene) -> list[Command]:
        """The effects that show ``scene`` to the player."""
        if self.native:
            self.resources.append(self._dialog_resource(scene))
            return [fx.dialog_show(str(self.dialog_id(scene)))]
        return self._tellraw_lines(scene)

    def _dialog_resource(self, scene: Scene) -> Resource:
        """One scene as a vanilla dialog screen."""
        from grimmcraft_compiler.dialect import Dialect

        dialect = Dialect(self.target)
        body = [
            {
                "type": "minecraft:plain_message",
                "contents": dialect.text_document(line),
            }
            for line in scene.lines
        ]
        # `type` first: these files are read by people as well as by the game.
        document: dict[str, Any] = {
            "type": (
                "minecraft:multi_action" if scene.is_menu else "minecraft:notice"
            ),
            "title": self.dialogue.speaker or self.dialogue.name,
            "body": body,
            "can_close_with_escape": True,
        }

        if scene.is_menu:
            # A conversation reads top-to-bottom, so one option per row.
            document["columns"] = 1
            document["actions"] = [
                {
                    "label": dialect.text_document(option.label),
                    "action": {
                        "type": "run_command",
                        # `run_command` takes the command without a leading '/'.
                        "command": f"function {self.dispatcher(option_event(index))}",
                    },
                }
                for index, option in enumerate(scene.options)
            ]
        else:
            if scene.goto is not None:
                document["action"] = {
                    "label": {"text": CONTINUE_LABEL},
                    "action": {
                        "type": "run_command",
                        "command": f"function {self.dispatcher(CONTINUE_EVENT)}",
                    },
                }
            # An ending scene omits `action` and gets the default OK button,
            # which simply closes the screen.

        return Resource(self.dialog_id(scene), "dialog", document)

    def _tellraw_lines(self, scene: Scene) -> list[Command]:
        """One scene as clickable chat, for targets without dialog screens."""
        commands: list[Command] = [
            fx.tellraw(self._spoken(line), target="@s") for line in scene.lines
        ]
        for index, option in enumerate(scene.options):
            commands.append(
                fx.tellraw(
                    option.label.styled(
                        click=run_command(
                            f"function {self.dispatcher(option_event(index))}"
                        ),
                        # Underlined so a clickable line is visibly different
                        # from something the NPC merely said.
                        underlined=True,
                    ),
                    target="@s",
                )
            )
        if scene.goto is not None:
            commands.append(
                fx.tellraw(
                    Text(
                        CONTINUE_LABEL,
                        underlined=True,
                        click=run_command(
                            f"function {self.dispatcher(CONTINUE_EVENT)}"
                        ),
                    ),
                    target="@s",
                )
            )
        return commands

    def _spoken(self, line: Text) -> Text:
        """A spoken line, prefixed with the speaker's name when there is one."""
        if self.dialogue.speaker is None:
            return line
        return Text(f"<{self.dialogue.speaker}> ").then(line)

    # --- the machine ---------------------------------------------------------
    def build(self) -> LoweredDialogue:
        builder: MachineBuilder[dict[str, Any]] = MachineBuilder(
            {}, name=self.dialogue.name
        )

        for scene in self.dialogue:
            # Effects first, then presentation: a scene that hands over an item
            # should have done so before the player reads about it.
            enter = [*scene.effects, *self.present(scene)]
            builder.state(scene.name, enter=enter, final=scene.is_end)

        for scene in self.dialogue:
            for index, option in enumerate(scene.options):
                builder.transition(
                    scene.name,
                    option_event(index),
                    to=option.goto,
                    commands=option.effects,
                    condition=_condition(option.condition),
                )
            if scene.goto is not None:
                builder.transition(scene.name, CONTINUE_EVENT, to=scene.goto)

        builder.initial(self.dialogue.start)
        return LoweredDialogue(
            machine=builder.build(),
            resources=self.resources,
            backend="dialog" if self.native else "tellraw",
        )


def _condition(condition: Any) -> Condition | None:
    """Translate the dialogue model's Condition into the machine's."""
    if condition is None:
        return None
    return Condition(
        ConditionName.SCORE_MATCHES,
        {
            "objective": condition.objective,
            "entry": condition.entry,
            "value": condition.value,
        },
    )


def lower_dialogue(
    dialogue: Dialogue, target: Target, *, namespace: str = "grimmcraft"
) -> LoweredDialogue:
    """Lower ``dialogue`` for ``target``, picking the best available backend.

    Raises :class:`ValueError` if the dialogue is structurally broken — dangling
    ``goto``, a scene with no ending — listing every problem at once.
    """
    problems = dialogue.problems()
    if problems:
        raise ValueError(
            f"dialogue '{dialogue.name}' is not valid:\n  - " + "\n  - ".join(problems)
        )
    return _DialogueLowering(dialogue, target, namespace).build()
