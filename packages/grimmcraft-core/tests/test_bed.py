"""The bed: a block that is also occupiable, and only after dark."""

from __future__ import annotations

import pytest

from grimmcraft_core.clock import MinecraftClock
from grimmcraft_core.coordinates import Coordinates
from grimmcraft_core.entity.npc import Npc
from grimmcraft_core.entity.player import Player
from grimmcraft_core.item.storage import PlaceableBlock
from grimmcraft_core.occupiable.bed import Bed
from grimmcraft_core.occupiable.occupancy import Sleepable

HERE = Coordinates(0.0, 64.0, 0.0)
BEDROOM = Coordinates(10.0, 64.0, 10.0)

NIGHT_HOUR = 22
DAY_HOUR = 12


@pytest.fixture
def alice() -> Player:
    return Player(position=HERE, name="alice")


@pytest.fixture
def bob() -> Player:
    return Player(position=HERE, name="bob")


@pytest.fixture
def villager() -> Npc:
    return Npc(position=HERE, name="Marlene")


@pytest.fixture
def night() -> MinecraftClock:
    clock = MinecraftClock()
    clock.set_time(NIGHT_HOUR)
    return clock


@pytest.fixture
def bed(night: MinecraftClock) -> Bed:
    """A bed placed in the world, after dark: the case where sleeping works."""
    placed = Bed(clock=night)
    placed.place(BEDROOM)
    return placed


# --- it is both things -------------------------------------------------------


def test_a_bed_is_a_block_and_occupiable(bed: Bed) -> None:
    """The claim the whole trait exists to allow, asserted rather than promised."""
    assert isinstance(bed, PlaceableBlock)
    assert isinstance(bed, Sleepable)


def test_a_bed_can_be_carried_before_it_is_placed() -> None:
    carried = Bed()
    assert not carried.is_placed
    assert carried.position is None


# --- where the sleeper ends up -----------------------------------------------


def test_sleeping_puts_the_sleeper_in_the_bed(bed: Bed, alice: Player) -> None:
    assert bed.enter(alice) is True
    assert alice.position == BEDROOM
    assert bed.sleeper is alice


def test_the_sleeper_goes_where_the_bed_is_not_somewhere_else(bed: Bed, alice: Player) -> None:
    """One position, so a bed placed here cannot put its sleeper there."""
    bed.enter(alice)
    assert alice.position == bed.position


def test_moving_the_bed_moves_where_the_next_sleeper_lands(bed: Bed, alice: Player) -> None:
    elsewhere = Coordinates(-20.0, 70.0, 5.0)
    bed.place(elsewhere)
    bed.enter(alice)
    assert alice.position == elsewhere


# --- one at a time -----------------------------------------------------------


def test_a_second_sleeper_is_refused(bed: Bed, alice: Player, bob: Player) -> None:
    bed.enter(alice)
    assert bed.enter(bob) is False
    assert bed.refusal_reason(bob) == "occupied"
    assert bed.is_occupied_by(alice), "the first sleeper stays"


def test_a_villager_and_a_player_compete_for_the_same_bed(
    bed: Bed, alice: Player, villager: Npc
) -> None:
    """Nothing in the bed asks which kind of entity it is holding."""
    assert bed.enter(villager) is True
    assert bed.enter(alice) is False


def test_getting_up_frees_the_bed(bed: Bed, alice: Player, bob: Player) -> None:
    bed.enter(alice)
    assert bed.exit() is alice
    assert bed.enter(bob) is True


# --- when you may sleep ------------------------------------------------------


def test_sleeping_is_refused_in_daylight(bed: Bed, night: MinecraftClock, alice: Player) -> None:
    night.set_time(DAY_HOUR)
    assert bed.enter(alice) is False
    assert bed.refusal_reason(alice) == "it is daytime"
    assert alice.position == HERE, "a refused sleeper is not moved"


def test_the_same_bed_accepts_once_night_falls(
    bed: Bed, night: MinecraftClock, alice: Player
) -> None:
    night.set_time(DAY_HOUR)
    assert bed.enter(alice) is False
    night.set_time(NIGHT_HOUR)
    assert bed.enter(alice) is True


@pytest.mark.parametrize("hour", [18, 20, 23, 0, 3, 5])
def test_night_wraps_around_midnight(hour: int) -> None:
    """Sunset to sunrise crosses the day boundary, so this is an `or`, not an `and`."""
    clock = MinecraftClock()
    clock.set_time(hour)
    assert Bed(clock=clock).is_night


@pytest.mark.parametrize("hour", [6, 9, 12, 17])
def test_daytime_is_the_rest_of_it(hour: int) -> None:
    clock = MinecraftClock()
    clock.set_time(hour)
    assert not Bed(clock=clock).is_night


def test_a_bed_without_a_clock_does_not_refuse_on_time(alice: Player) -> None:
    """A bed that has not been told the hour cannot claim it is the wrong one."""
    clockless = Bed()
    clockless.place(BEDROOM)
    assert clockless.is_night
    assert clockless.enter(alice) is True


# --- a bed you are carrying is not somewhere to sleep ------------------------


def test_an_unplaced_bed_refuses(alice: Player, night: MinecraftClock) -> None:
    carried = Bed(clock=night)
    assert carried.enter(alice) is False
    assert carried.refusal_reason(alice) == "not placed"
    assert alice.position == HERE


def test_occupied_is_reported_before_the_bed_s_own_reasons(
    bed: Bed, night: MinecraftClock, alice: Player
) -> None:
    """Deferring upwards first keeps "already inside" worded in one place."""
    bed.enter(alice)
    night.set_time(DAY_HOUR)
    assert bed.refusal_reason(alice) == "already inside"


# --- interacting and breaking ------------------------------------------------


def test_interacting_with_a_bed_is_trying_to_sleep(bed: Bed, alice: Player) -> None:
    bed.interact(alice)
    assert bed.sleeper is alice
    assert alice.position == BEDROOM


def test_interacting_in_daylight_records_the_attempt_but_does_not_sleep(
    bed: Bed, night: MinecraftClock, alice: Player
) -> None:
    night.set_time(DAY_HOUR)
    bed.interact(alice)
    assert bed.sleeper is None
    assert bed.last_opened_by is alice


def test_breaking_the_bed_turfs_the_sleeper_out(bed: Bed, alice: Player) -> None:
    """Otherwise the broken bed goes on refusing everyone as still occupied."""
    bed.enter(alice)
    bed.break_block()
    assert not bed.is_placed
    assert bed.sleeper is None


def test_a_broken_bed_can_be_placed_and_slept_in_again(
    bed: Bed, alice: Player, bob: Player
) -> None:
    bed.enter(alice)
    bed.break_block()
    bed.place(BEDROOM)
    assert bed.enter(bob) is True
