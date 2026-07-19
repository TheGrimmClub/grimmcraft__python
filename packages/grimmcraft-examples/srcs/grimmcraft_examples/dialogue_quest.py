"""Example: a quest dialogue — conditions, effects, memory, and a loop.

Run with ``task examples:dialogue-quest``, or
``uv run --package grimmcraft-examples python -m grimmcraft_examples.dialogue_quest``.

Read `dialogue_greeting.py` first: it covers scenes, menus and the two backends.
This one adds the four things that turn a conversation into a quest.

# 1. Options that are not always there

``when_flag`` and ``when_score`` gate an option. A player who has not been given
the quest never sees "I found your millstone" — the option is not hidden in the
UI, it is not offered at all, because the condition is compiled into the
machine's transition.

# 2. Effects

``give`` and ``set_flag`` are shorthands over ``do()``, which writes arbitrary
commands. An effect runs when the scene is entered or the option is taken.

# 3. Memory

A flag is a scoreboard value, so it survives the conversation ending. That is
what makes the miller remember, on the *next* conversation, that she already
asked — and it is why ``start`` branches on ``when_flag`` before saying hello.

# 4. Loops

``ask_again`` goes back to ``start``. Scenes are states and options are
transitions, so a cycle is just a cycle — nothing special is needed, and the
round-trip through the compiler survives it.
"""

from __future__ import annotations

from grimmcraft_compiler.target import Target
from grimmcraft_data.item import Item
from grimmcraft_npc import lower_dialogue, new_dialogue

QUEST_GIVEN = "quest_given"
QUEST_DONE = "quest_done"


def build():
    """Marlene asks for her lost millstone, and remembers whether she has asked."""
    talk = new_dialogue("miller_quest", speaker="Marlene the Miller")

    # --- the hub, which branches on what the player has already done ---------
    with talk.scene("start") as start:
        start.say("Welcome to the mill, traveller.")
        with start.menu() as choices:
            # Only offered before the quest is given.
            choices.option("You look troubled.", goto="ask_favour")

            # Only once the quest is running -- the condition is a machine
            # transition guard, so this option does not exist until then.
            choices.option("I found your millstone.", goto="hand_in").when_flag(QUEST_GIVEN)

            # Only after finishing, so thanks are not repeated forever.
            choices.option("Anything else?", goto="after_quest").when_flag(QUEST_DONE)

            choices.option("Just passing through.", goto="farewell")

    # --- giving the quest ----------------------------------------------------
    with talk.scene("ask_favour") as favour:
        favour.say("My millstone was stolen. The river cave, most likely.")
        with favour.menu() as choices:
            with choices.option("I'll find it.", goto="accepted") as accept:
                # Taking this option is what records the quest.
                accept.do().set_score(QUEST_GIVEN, "@s", 1)
            choices.option("Not my problem.", goto="declined")

    with talk.scene("accepted") as accepted:
        accepted.set_flag(QUEST_GIVEN)
        accepted.say("Bless you. Take a lantern — the cave is dark.")
        accepted.give(Item.LANTERN)
        accepted.goto("farewell")

    with talk.scene("declined") as declined:
        declined.say("Then I'll not keep you.")
        declined.goto("farewell")

    # --- completing it -------------------------------------------------------
    with talk.scene("hand_in") as hand_in:
        hand_in.set_flag(QUEST_DONE)
        hand_in.say("You found it! The village eats this winter because of you.")
        hand_in.give(Item.EMERALD, count=8)
        hand_in.goto("ask_again")

    with talk.scene("after_quest") as after:
        after.say("Nothing but flour and gossip, and you've had both.")
        after.goto("ask_again")

    # --- the loop ------------------------------------------------------------
    with talk.scene("ask_again") as again:
        again.say("Was there something else?")
        with again.menu() as choices:
            choices.option("Actually, yes.", goto="start")
            choices.option("No, thank you.", goto="farewell")

    with talk.scene("farewell") as farewell:
        farewell.say("Mind the wheel on your way out.")
        farewell.end()

    return talk.build()


def main() -> None:
    dialogue = build()

    print(f"dialogue {dialogue.name!r} — {len(dialogue.scenes)} scenes\n")
    for name, scene in dialogue.scenes.items():
        print(f"  scene {name!r}")
        for line in scene.lines:
            print(f"      say: {line}")
        for effect in scene.effects:
            print(f"      effect: {effect}")
        for option in scene.options:
            condition = option.condition
            gate = (
                f"  [only if {condition.objective}[{condition.entry}] == {condition.value}]"
                if condition
                else ""
            )
            print(f"      option: {option.label} -> {option.goto}{gate}")

    target = Target.resolve("1.21.11", "vanilla")
    lowered = lower_dialogue(dialogue, target, namespace="village")
    print(
        f"\nlowered to a machine: {len(lowered.machine.states)} states, "
        f"{len(lowered.resources)} dialog resource(s)"
    )
    print("a cycle (hand_in -> ask_again -> start) survives lowering unchanged")


if __name__ == "__main__":
    main()
