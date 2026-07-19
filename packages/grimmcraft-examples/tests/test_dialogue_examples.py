"""The dialogue examples.

Examples are documentation that runs, so these tests exist to make sure the
documentation stays true: an example that silently stops working teaches the
wrong thing to whoever copies it next.
"""

from __future__ import annotations

import pytest

from grimmcraft_compiler.target import Target
from grimmcraft_examples import dialogue_greeting, dialogue_quest
from grimmcraft_npc import lower_dialogue, uses_dialog_screens

VERSION_WITHOUT_DIALOGS = "1.21.4"
VERSION_WITH_DIALOGS = "1.21.11"


# --- the simple example ------------------------------------------------------


def test_the_greeting_builds() -> None:
    dialogue = dialogue_greeting.build()
    assert dialogue.start == "start"
    assert set(dialogue.scenes) == {"start", "about", "farewell"}


def test_the_greeting_offers_two_ways_out_of_the_first_scene() -> None:
    scenes = dialogue_greeting.build().scenes
    assert [option.goto for option in scenes["start"].options] == ["about", "farewell"]


def test_a_scene_without_a_menu_falls_through() -> None:
    """`about` says its line and continues to `farewell` with no player choice."""
    about = dialogue_greeting.build().scenes["about"]
    assert about.options == ()


@pytest.mark.parametrize("version", [VERSION_WITHOUT_DIALOGS, VERSION_WITH_DIALOGS])
def test_the_greeting_lowers_on_both_backends(version: str) -> None:
    """The same conversation, whichever way it is shown."""
    target = Target.resolve(version, "vanilla")
    lowered = lower_dialogue(dialogue_greeting.build(), target, namespace="village")
    assert len(lowered.machine.states) == 3


def test_only_the_newer_target_uses_dialog_screens() -> None:
    """The point of the example: the backend differs, the dialogue does not."""
    assert not uses_dialog_screens(Target.resolve(VERSION_WITHOUT_DIALOGS, "vanilla"))
    assert uses_dialog_screens(Target.resolve(VERSION_WITH_DIALOGS, "vanilla"))


# --- the quest example -------------------------------------------------------


def test_the_quest_builds() -> None:
    dialogue = dialogue_quest.build()
    assert len(dialogue.scenes) == 8


def test_gated_options_carry_a_condition() -> None:
    """Two of the four options in `start` only exist once a flag is set."""
    start = dialogue_quest.build().scenes["start"]
    gated = [option for option in start.options if option.condition is not None]
    assert len(gated) == 2
    assert {option.goto for option in gated} == {"hand_in", "after_quest"}


def test_ungated_options_have_no_condition() -> None:
    start = dialogue_quest.build().scenes["start"]
    open_always = [option for option in start.options if option.condition is None]
    assert {option.goto for option in open_always} == {"ask_favour", "farewell"}


def test_accepting_the_quest_has_effects() -> None:
    accepted = dialogue_quest.build().scenes["accepted"]
    assert accepted.effects, "setting the flag and giving the lantern are effects"


def test_the_quest_contains_a_cycle() -> None:
    """hand_in -> ask_again -> start, which lowering must survive."""
    scenes = dialogue_quest.build().scenes
    assert scenes["hand_in"].goto == "ask_again"
    assert "start" in {option.goto for option in scenes["ask_again"].options}


def test_the_quest_lowers_despite_the_cycle() -> None:
    target = Target.resolve(VERSION_WITH_DIALOGS, "vanilla")
    lowered = lower_dialogue(dialogue_quest.build(), target, namespace="village")
    assert len(lowered.machine.states) == 8


def test_every_option_goes_somewhere_that_exists() -> None:
    """A typo in a `goto` would otherwise only show up in game."""
    for example in (dialogue_greeting, dialogue_quest):
        dialogue = example.build()
        for name, scene in dialogue.scenes.items():
            for option in scene.options:
                assert option.goto in dialogue.scenes, f"{name} -> {option.goto}"
            if scene.goto is not None:
                assert scene.goto in dialogue.scenes, f"{name} -> {scene.goto}"


# --- both run ----------------------------------------------------------------


@pytest.mark.parametrize("example", [dialogue_greeting, dialogue_quest])
def test_main_runs_and_prints(example, capsys: pytest.CaptureFixture[str]) -> None:
    example.main()
    assert capsys.readouterr().out.strip()
