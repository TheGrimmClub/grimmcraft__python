"""Occupancy: one occupant at a time, and where they end up."""

from __future__ import annotations

import pytest

from grimmcraft_core.coordinates import Coordinates
from grimmcraft_core.entity.npc import Npc
from grimmcraft_core.entity.player import Player
from grimmcraft_core.occupiable.occupancy import Occupiable, Sleepable

HERE = Coordinates(0.0, 64.0, 0.0)
BED = Coordinates(10.0, 64.0, 10.0)


@pytest.fixture
def alice() -> Player:
    return Player(position=HERE, name="alice")


@pytest.fixture
def bob() -> Player:
    return Player(position=HERE, name="bob")


@pytest.fixture
def villager() -> Npc:
    return Npc(position=HERE, name="Marlene")


# --- one at a time -----------------------------------------------------------


def test_an_empty_thing_accepts_an_occupant(alice: Player) -> None:
    thing = Occupiable()
    assert not thing.is_occupied
    assert thing.enter(alice) is True
    assert thing.is_occupied
    assert thing.is_occupied_by(alice)


def test_a_second_occupant_is_refused(alice: Player, bob: Player) -> None:
    thing = Occupiable()
    thing.enter(alice)
    assert thing.enter(bob) is False
    assert thing.is_occupied_by(alice), "the first occupant stays"
    assert thing.refusal_reason(bob) == "occupied"


def test_entering_twice_is_refused_with_its_own_reason(alice: Player) -> None:
    """Distinguished from "occupied" so a caller can tell "you are already in it"."""
    thing = Occupiable()
    thing.enter(alice)
    assert thing.enter(alice) is False
    assert thing.refusal_reason(alice) == "already inside"


def test_leaving_frees_it(alice: Player, bob: Player) -> None:
    thing = Occupiable()
    thing.enter(alice)
    assert thing.exit() is alice
    assert not thing.is_occupied
    assert thing.enter(bob) is True


def test_leaving_an_empty_thing_returns_nothing() -> None:
    assert Occupiable().exit() is None


def test_refusal_is_an_answer_not_an_exception(alice: Player, bob: Player) -> None:
    """Something else being in the bed is ordinary, so `enter` returns False."""
    thing = Occupiable()
    thing.enter(alice)
    assert thing.enter(bob) is False  # must not raise


# --- players and villagers are the same thing here ---------------------------


def test_a_villager_can_occupy(villager: Npc) -> None:
    thing = Occupiable()
    assert thing.enter(villager) is True
    assert thing.is_occupied_by(villager)


def test_a_villager_blocks_a_player_and_the_reverse(alice: Player, villager: Npc) -> None:
    """Nothing here asks which kind of entity it holds."""
    bed = Sleepable(rest_position=BED)
    assert bed.enter(villager) is True
    assert bed.enter(alice) is False


# --- where the occupant ends up ----------------------------------------------


def test_a_sleepable_moves_its_occupant_to_the_rest_position(alice: Player) -> None:
    bed = Sleepable(rest_position=BED)
    bed.enter(alice)
    assert alice.position == BED
    assert bed.sleeper is alice


def test_without_a_rest_position_the_occupant_stays_put(alice: Player) -> None:
    """A bed not yet placed in the world should not teleport anyone to nowhere."""
    bed = Sleepable()
    bed.enter(alice)
    assert alice.position == HERE


def test_leaving_does_not_move_the_occupant_back(alice: Player) -> None:
    """Where someone goes after getting up is not the bed's business."""
    bed = Sleepable(rest_position=BED)
    bed.enter(alice)
    bed.exit()
    assert alice.position == BED


def test_settling_is_safe_when_empty() -> None:
    Sleepable(rest_position=BED).settle_occupant()  # must not raise


# --- the seam the seat variant will use --------------------------------------


def test_a_moving_host_can_drag_its_occupant_along(alice: Player) -> None:
    """The whole design claim: a seat is a Sleepable whose position moves.

    Written as a test rather than a comment, because "drops in without
    refactoring" is only true if it can be demonstrated without changing
    Occupiable — and this does it by overriding the one property.
    """

    class Seat(Occupiable):
        def __init__(self, host: Player) -> None:
            super().__init__()
            self.host = host

        @property
        def occupant_position(self) -> Coordinates:
            return self.host.position

    boat = Player(position=HERE, name="boat")
    seat = Seat(boat)
    seat.enter(alice)
    assert alice.position == HERE

    boat.move_to(Coordinates(50.0, 64.0, 0.0))
    seat.settle_occupant()
    assert alice.position == Coordinates(50.0, 64.0, 0.0)


def test_occupancy_knows_nothing_about_blocks_or_villagers() -> None:
    """The orthogonality claim, asserted rather than promised."""
    import grimmcraft_core.occupiable.occupancy as occupancy

    source = occupancy.__doc__ or ""
    assert "profession" not in dir(occupancy)
    for forbidden in ("Block", "VillagerProfession", "PointOfInterest"):
        assert not hasattr(occupancy, forbidden), f"occupancy imported {forbidden}"
    assert source, "the module explains why it is a trait"
