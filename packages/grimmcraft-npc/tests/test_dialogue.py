"""Dialogue: the model, the builder, and both presentation backends."""

from __future__ import annotations

import pytest

from grimmcraft_compiler.dialect import Dialect
from grimmcraft_compiler.target import Target
from grimmcraft_control.machine import CommandName
from grimmcraft_core.entity.dialogue import option_event
from grimmcraft_npc import lower_dialogue, new_dialogue, uses_dialog_screens

#: Either side of the 1.21.6 dialog-registry threshold.
NATIVE = "1.21.11"
FALLBACK = "1.21.4"


def miller():  # type: ignore[no-untyped-def]
    """A small branching conversation with a guard, a loop and two endings."""
    talk = new_dialogue("miller", speaker="Marlene the Miller")
    with talk.scene("start") as start:
        start.say("Welcome to the mill.")
        with start.menu() as choices:
            choices.option("Who are you?", goto="about")
            choices.option("Bread?", goto="trade")
    with talk.scene("about") as about:
        about.say("A miller.")
        about.goto("start")
    with talk.scene("trade") as trade:
        with trade.menu() as choices:
            choices.option("Buy.", goto="bought").when_score("emeralds", "@s", 2)
            choices.option("No.", goto="start")
    with talk.scene("bought") as bought:
        bought.give("minecraft:bread").set_flag("bought_bread")
        bought.end()
    return talk.build()


# --- the model ---------------------------------------------------------------
def test_scenes_keep_declaration_order() -> None:
    assert list(miller().scenes) == ["start", "about", "trade", "bought"]


def test_first_scene_is_the_start_by_default() -> None:
    assert miller().start == "start"


def test_a_dangling_goto_is_rejected_at_build() -> None:
    talk = new_dialogue("broken")
    with talk.scene("start") as start:
        start.goto("nowhere")
    with pytest.raises(ValueError, match="'nowhere', which is not a scene"):
        talk.build()


def test_a_scene_with_no_ending_is_rejected() -> None:
    """A scene that neither branches, jumps nor ends would hang the player."""
    talk = new_dialogue("broken")
    with talk.scene("start") as start:
        start.say("...")
    with pytest.raises(ValueError, match="neither offers options"):
        talk.build()


def test_two_endings_are_rejected() -> None:
    talk = new_dialogue("broken")
    with talk.scene("start") as start:
        start.goto("other")
        start.end()
    with talk.scene("other") as other:
        other.end()
    with pytest.raises(ValueError, match="more than one ending"):
        talk.build()


def test_unreachable_scenes_are_reported() -> None:
    talk = new_dialogue("orphan")
    with talk.scene("start") as start:
        start.end()
    with talk.scene("lost") as lost:
        lost.end()
    assert talk.build().unreachable() == ["lost"]


# --- lowering to a machine ---------------------------------------------------
def test_scenes_become_states_and_options_become_transitions() -> None:
    machine = lower_dialogue(miller(), Target.resolve(NATIVE, "vanilla")).machine
    assert list(machine.states) == ["start", "about", "trade", "bought"]
    assert machine.initial == "start"

    edges = {(t.source, t.event, t.target) for t in machine.transitions}
    assert ("start", option_event(0), "about") in edges
    assert ("start", option_event(1), "trade") in edges
    assert ("about", "continue", "start") in edges, "a goto is a transition too"


def test_a_guarded_option_becomes_a_condition() -> None:
    machine = lower_dialogue(miller(), Target.resolve(NATIVE, "vanilla")).machine
    (buy,) = [
        t for t in machine.transitions
        if t.source == "trade" and t.target == "bought"
    ]
    assert buy.condition is not None
    assert buy.condition.payload["objective"] == "emeralds"
    assert buy.condition.payload["value"] == 2


def test_scene_effects_run_before_the_scene_is_shown() -> None:
    """An item handed over should be in hand before the player reads about it."""
    machine = lower_dialogue(miller(), Target.resolve(NATIVE, "vanilla")).machine
    names = [c.name for c in machine.states["bought"].enter]
    assert names.index(CommandName.GIVE) < names.index(CommandName.DIALOG_SHOW)


def test_ending_scenes_are_final() -> None:
    machine = lower_dialogue(miller(), Target.resolve(NATIVE, "vanilla")).machine
    assert machine.states["bought"].is_final


# --- the native dialog backend -----------------------------------------------
def test_native_backend_is_chosen_from_1_21_6() -> None:
    assert uses_dialog_screens(Target.resolve(NATIVE, "vanilla"))
    assert not uses_dialog_screens(Target.resolve(FALLBACK, "vanilla"))


def test_each_scene_becomes_a_dialog_resource() -> None:
    lowered = lower_dialogue(
        miller(), Target.resolve(NATIVE, "vanilla"), namespace="village"
    )
    assert lowered.backend == "dialog"
    ids = {str(r.id) for r in lowered.resources}
    assert ids == {
        "village:miller/start", "village:miller/about",
        "village:miller/trade", "village:miller/bought",
    }
    assert {r.category for r in lowered.resources} == {"dialog"}


def test_a_menu_becomes_a_multi_action_dialog() -> None:
    lowered = lower_dialogue(
        miller(), Target.resolve(NATIVE, "vanilla"), namespace="village"
    )
    start = next(r for r in lowered.resources if r.id.path.endswith("/start"))

    assert start.content["type"] == "minecraft:multi_action"
    assert start.content["title"] == "Marlene the Miller"
    labels = [a["label"]["text"] for a in start.content["actions"]]
    assert labels == ["Who are you?", "Bread?"]


def test_buttons_call_the_machines_own_dispatchers() -> None:
    """The whole thing only works if a button runs the function lowering emits."""
    target = Target.resolve(NATIVE, "vanilla")
    lowered = lower_dialogue(miller(), target, namespace="village")
    start = next(r for r in lowered.resources if r.id.path.endswith("/start"))

    commanded = {a["action"]["command"] for a in start.content["actions"]}
    assert commanded == {
        "function village:miller/on_choice_0",
        "function village:miller/on_choice_1",
    }
    # …and those functions exist in the compiled pack.
    from grimmcraft_compiler.lower import lower

    pack = lower([lowered.machine], "village", description="d")
    assert "village:miller/on_choice_0" in pack.function_ids()


def test_a_goto_scene_becomes_a_notice_with_a_continue_button() -> None:
    lowered = lower_dialogue(
        miller(), Target.resolve(NATIVE, "vanilla"), namespace="village"
    )
    about = next(r for r in lowered.resources if r.id.path.endswith("/about"))
    assert about.content["type"] == "minecraft:notice"
    assert about.content["action"]["action"]["command"] == (
        "function village:miller/on_continue"
    )


def test_an_ending_scene_has_no_action_button() -> None:
    """Omitting `action` leaves the default OK button, which just closes."""
    lowered = lower_dialogue(
        miller(), Target.resolve(NATIVE, "vanilla"), namespace="village"
    )
    bought = next(r for r in lowered.resources if r.id.path.endswith("/bought"))
    assert bought.content["type"] == "minecraft:notice"
    assert "action" not in bought.content


# --- the tellraw fallback ----------------------------------------------------
def test_fallback_backend_emits_no_resources() -> None:
    lowered = lower_dialogue(miller(), Target.resolve(FALLBACK, "vanilla"))
    assert lowered.backend == "tellraw"
    assert lowered.resources == []


def test_fallback_options_are_clickable_tellraw() -> None:
    target = Target.resolve(FALLBACK, "vanilla")
    lowered = lower_dialogue(miller(), target, namespace="village")
    dialect = Dialect(target)

    rendered = [dialect.render(c) for c in lowered.machine.states["start"].enter]
    clickable = [line for line in rendered if "clickEvent" in line]
    assert len(clickable) == 2
    # Pre-1.21.5 the command lives in `value` and keeps its leading slash.
    assert '"value":"/function village:miller/on_choice_0"' in clickable[0]


def test_fallback_prefixes_lines_with_the_speaker() -> None:
    target = Target.resolve(FALLBACK, "vanilla")
    lowered = lower_dialogue(miller(), target)
    rendered = Dialect(target).render(lowered.machine.states["start"].enter[0])
    assert "<Marlene the Miller> " in rendered


def test_both_backends_produce_the_same_behaviour() -> None:
    """Only presentation may differ — states, transitions and guards must not."""
    native = lower_dialogue(miller(), Target.resolve(NATIVE, "vanilla")).machine
    fallback = lower_dialogue(miller(), Target.resolve(FALLBACK, "vanilla")).machine

    def edges(machine):  # type: ignore[no-untyped-def]
        return {
            (t.source, t.event, t.target, t.condition is not None)
            for t in machine.transitions
        }

    assert list(native.states) == list(fallback.states)
    assert native.initial == fallback.initial
    assert edges(native) == edges(fallback)
