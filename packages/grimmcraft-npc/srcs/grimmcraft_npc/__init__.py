"""grimmcraft-npc — branching dialogue and Taterzens NPCs.

Dialogue is written the way Ren'Py writes it — named scenes that say lines and
offer menus — and *is* a state machine, so it lowers to
:class:`~grimmcraft_control.machine.Machine` and inherits the whole existing
pipeline: validation, compilation, the round-trip guarantee, and decompilation
back to readable Python.

    talk = new_dialogue("miller", speaker="Marlene the Miller")

    with talk.scene("start") as start:
        start.say("Welcome to the mill, traveller.")
        with start.menu() as choices:
            choices.option("Who are you?", goto="about")
            choices.option("Goodbye.", goto="farewell")
    ...
    lowered = lower_dialogue(talk.build(), target, namespace="village")
    compile_machines([lowered.machine], target, namespace="village",
                     resources=lowered.resources)

How a scene is *shown* depends on the target, and only that part does:

* **1.21.6+** — a real vanilla ``dialog`` screen with buttons;
* **earlier** — clickable ``tellraw`` chat lines.

The behaviour is identical either way, because both drive the same machine.
"""

from __future__ import annotations

from grimmcraft_core.dialogue import (
    Condition,
    Dialogue,
    Option,
    Scene,
    option_event,
)
from grimmcraft_core.text import Text, run_command, show_dialog, suggest_command
from grimmcraft_npc.builder import (
    FLAG_OBJECTIVE,
    DialogueBuilder,
    MenuDraft,
    OptionDraft,
    SceneDraft,
    new_dialogue,
)
from grimmcraft_npc.lower import (
    CONTINUE_EVENT,
    DIALOGS_SINCE,
    LoweredDialogue,
    lower_dialogue,
    uses_dialog_screens,
)

__all__ = [
    # authoring
    "new_dialogue",
    "DialogueBuilder",
    "SceneDraft",
    "MenuDraft",
    "OptionDraft",
    "FLAG_OBJECTIVE",
    # the model
    "Dialogue",
    "Scene",
    "Option",
    "Condition",
    "option_event",
    "Text",
    "run_command",
    "suggest_command",
    "show_dialog",
    # lowering
    "lower_dialogue",
    "LoweredDialogue",
    "uses_dialog_screens",
    "DIALOGS_SINCE",
    "CONTINUE_EVENT",
]
