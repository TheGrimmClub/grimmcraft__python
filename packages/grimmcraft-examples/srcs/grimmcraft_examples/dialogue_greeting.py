"""Example: the smallest branching dialogue — a miller who answers one question.

Run with ``task examples:dialogue-greeting``, or
``uv run --package grimmcraft-examples python -m grimmcraft_examples.dialogue_greeting``.

# What to notice

A dialogue is written the way Ren'Py writes one: named **scenes** that say lines
and offer a **menu**. Each ``with`` block is one scene, and closing the block
finishes it — so the shape of the code is the shape of the conversation.

    with talk.scene("start") as start:      label start:
        start.say("Welcome.")                  m "Welcome."
        with start.menu() as choices:          menu:
            choices.option("Who?",                 "Who?":
                           goto="about")               jump about

And a dialogue *is* a state machine: scenes are states, options are transitions,
the option a player clicks is the event. Nothing here mentions Minecraft — the
target decides whether this becomes a 1.21.6 ``dialog`` screen or clickable
``tellraw`` lines, and the conversation is identical either way.

Read `dialogue_quest.py` next: conditions, effects, and a scene that loops.
"""

from __future__ import annotations

from grimmcraft_compiler.target import Target
from grimmcraft_npc import lower_dialogue, new_dialogue, uses_dialog_screens


def build():
    """A miller with three things to say and two ways to leave."""
    talk = new_dialogue("miller", speaker="Marlene the Miller")

    with talk.scene("start") as start:
        start.say("Welcome to the mill, traveller.")
        with start.menu() as choices:
            choices.option("Who are you?", goto="about")
            choices.option("Just passing through.", goto="farewell")

    with talk.scene("about") as about:
        about.say("Marlene. I grind the village's grain, and I hear its gossip.")
        # No menu: the scene falls through to the one it names.
        about.goto("farewell")

    with talk.scene("farewell") as farewell:
        farewell.say("Mind the wheel on your way out.")
        farewell.end()

    return talk.build()


def main() -> None:
    dialogue = build()

    print(f"dialogue {dialogue.name!r}, speaker {dialogue.speaker!r}")
    print(f"  {len(dialogue.scenes)} scenes, starting at {dialogue.start!r}\n")

    for name, scene in dialogue.scenes.items():
        print(f"  scene {name!r}")
        for line in scene.lines:
            print(f"      say: {line}")
        for option in scene.options:
            print(f"      option: {option.label} -> {option.goto}")

    # The same dialogue on two targets, to show the backend is the only thing
    # that changes -- the conversation above does not know which one it gets.
    for version in ("1.21.4", "1.21.11"):
        target = Target.resolve(version, "vanilla")
        lowered = lower_dialogue(dialogue, target, namespace="village")
        backend = "dialog screens" if uses_dialog_screens(target) else "tellraw chat"
        print(
            f"\n{version}: {backend}"
            f" — {len(lowered.machine.states)} states,"
            f" {len(lowered.resources)} extra resource(s)"
        )


if __name__ == "__main__":
    main()
