"""The game session: roster, modes, and rules that are named the way the game names them."""

from __future__ import annotations

import pytest

from grimmcraft_core.game import Game, GameModeType
from grimmcraft_data.game_rule import GameRule, game_rule


@pytest.fixture
def game() -> Game:
    return Game()


# --- the rule names ----------------------------------------------------------


def test_no_rule_is_spelled_with_an_underscore() -> None:
    """The bug this replaced: a hand-written `do_daylight_cycle`.

    Minecraft ignores an unknown rule name rather than rejecting it, so the
    wrong spelling produced a command that did nothing and said nothing.
    """
    assert [rule for rule in GameRule if "_" in rule.string_id] == []


def test_the_daylight_rule_is_camel_case() -> None:
    assert GameRule.DO_DAYLIGHT_CYCLE.string_id == "doDaylightCycle"


def test_rules_carry_the_vanilla_label() -> None:
    assert GameRule.DO_DAYLIGHT_CYCLE.label
    assert game_rule("doDaylightCycle") is GameRule.DO_DAYLIGHT_CYCLE


def test_an_unknown_name_resolves_to_nothing() -> None:
    assert game_rule("do_daylight_cycle") is None, "the old spelling is not a rule"


# --- reading and setting -----------------------------------------------------


def test_an_unset_rule_reads_as_none(game: Game) -> None:
    """It used to raise KeyError, so any read on a fresh session failed."""
    assert game.rule(GameRule.KEEP_INVENTORY) is None
    assert not game.is_rule_set(GameRule.KEEP_INVENTORY)


def test_an_unset_rule_can_take_a_caller_supplied_default(game: Game) -> None:
    """Core ships no vanilla defaults, so the caller supplies one if they have it."""
    assert game.rule(GameRule.RANDOM_TICK_SPEED, default=3) == 3


def test_setting_and_reading(game: Game) -> None:
    game.set_rule(GameRule.KEEP_INVENTORY, True)
    assert game.rule(GameRule.KEEP_INVENTORY) is True
    assert game.is_rule_set(GameRule.KEEP_INVENTORY)


def test_integer_rules_hold_integers(game: Game) -> None:
    game.set_rule(GameRule.RANDOM_TICK_SPEED, 10)
    assert game.rule(GameRule.RANDOM_TICK_SPEED) == 10


def test_rules_returns_a_copy(game: Game) -> None:
    game.set_rule(GameRule.KEEP_INVENTORY, True)
    game.rules[GameRule.KEEP_INVENTORY] = False
    assert game.rule(GameRule.KEEP_INVENTORY) is True


# --- players -----------------------------------------------------------------


def test_a_new_player_inherits_the_seed_mode(game: Game) -> None:
    game.add_player("alice")
    assert game.mode("alice") is GameModeType.SURVIVAL


def test_setting_a_mode(game: Game) -> None:
    game.add_player("alice")
    game.set_mode("alice", GameModeType.CREATIVE)
    assert game.mode("alice") is GameModeType.CREATIVE


def test_setting_a_mode_for_a_stranger_is_rejected(game: Game) -> None:
    """It used to succeed and then be lost, since mode() rejects the same name."""
    with pytest.raises(ValueError, match="not found"):
        game.set_mode("nobody", GameModeType.CREATIVE)


def test_reading_a_mode_for_a_stranger_is_rejected(game: Game) -> None:
    with pytest.raises(ValueError, match="not found"):
        game.mode("nobody")


def test_removing_a_player(game: Game) -> None:
    game.add_player("alice")
    game.remove_player("alice")
    assert not game.has_player("alice")
    game.remove_player("alice")  # no-op, must not raise


# --- banning -----------------------------------------------------------------


def test_a_ban_keeps_the_player_out(game: Game) -> None:
    """ban_player used to just call remove_player, so a ban lasted until reconnect."""
    game.add_player("griefer")
    game.ban_player("griefer")

    assert not game.has_player("griefer")
    assert game.is_banned("griefer")
    with pytest.raises(ValueError, match="banned"):
        game.add_player("griefer")


def test_unbanning_lets_them_back_in(game: Game) -> None:
    game.ban_player("griefer")
    game.unban_player("griefer")
    assert not game.is_banned("griefer")
    game.add_player("griefer")
    assert game.has_player("griefer")


def test_unbanning_someone_never_banned_is_harmless(game: Game) -> None:
    game.unban_player("stranger")


def test_unbanning_does_not_re_add(game: Game) -> None:
    game.add_player("griefer")
    game.ban_player("griefer")
    game.unban_player("griefer")
    assert not game.has_player("griefer")
