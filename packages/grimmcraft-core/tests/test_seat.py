"""The seat: an occupant carried by a moving host."""

from __future__ import annotations

import pytest

from grimmcraft_core.coordinates import Coordinates
from grimmcraft_core.entity.npc import Npc
from grimmcraft_core.entity.player import Player
from grimmcraft_core.occupiable.occupancy import Occupiable
from grimmcraft_core.occupiable.seat import Seat

HERE = Coordinates(0.0, 64.0, 0.0)
THERE = Coordinates(50.0, 64.0, 0.0)
SADDLE_HEIGHT = Coordinates(0.0, 1.0, 0.0)


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
def boat() -> Player:
    """Any `Positioned` will do as a host — that is the point of the protocol."""
    return Player(position=HERE, name="boat")


# --- it is an Occupiable like any other --------------------------------------


def test_a_seat_is_occupiable(boat: Player) -> None:
    assert isinstance(Seat(host=boat), Occupiable)


def test_a_second_passenger_is_refused(boat: Player, alice: Player, bob: Player) -> None:
    """A seat holds one, so "the seat is taken" has an answer."""
    seat = Seat(host=boat)
    assert seat.enter(alice) is True
    assert seat.enter(bob) is False
    assert seat.refusal_reason(bob) == "occupied"


def test_a_villager_can_be_carried(boat: Player, villager: Npc) -> None:
    seat = Seat(host=boat)
    assert seat.enter(villager) is True
    assert villager.position == HERE


def test_getting_out_frees_the_seat(boat: Player, alice: Player, bob: Player) -> None:
    seat = Seat(host=boat)
    seat.enter(alice)
    assert seat.exit() is alice
    assert seat.enter(bob) is True


# --- the host carries the occupant -------------------------------------------


def test_sitting_down_puts_the_occupant_on_the_host(boat: Player, alice: Player) -> None:
    alice.teleport(THERE)
    Seat(host=boat).enter(alice)
    assert alice.position == HERE, "the occupant is brought to the host"


def test_the_occupant_follows_the_host(boat: Player, alice: Player) -> None:
    """The whole reason a seat differs from a bed."""
    seat = Seat(host=boat)
    seat.enter(alice)

    boat.move_to(THERE)
    seat.settle_occupant()
    assert alice.position == THERE


def test_the_position_is_read_fresh_not_cached(boat: Player, alice: Player) -> None:
    """Computed from the host on every read, so it cannot go stale."""
    seat = Seat(host=boat)
    seat.enter(alice)
    boat.move_to(THERE)
    assert seat.occupant_position == THERE, "without any settle call in between"


def test_an_empty_seat_carries_nothing(boat: Player) -> None:
    seat = Seat(host=boat)
    boat.move_to(THERE)
    seat.settle_occupant()  # must not raise


def test_getting_out_leaves_the_occupant_where_they_were(boat: Player, alice: Player) -> None:
    """Where someone goes after getting out is not the seat's business."""
    seat = Seat(host=boat)
    seat.enter(alice)
    boat.move_to(THERE)
    seat.settle_occupant()
    seat.exit()

    boat.move_to(Coordinates(99.0, 64.0, 0.0))
    seat.settle_occupant()
    assert alice.position == THERE, "no longer carried"


# --- riding above the host ---------------------------------------------------


def test_a_rider_sits_above_the_host(boat: Player, alice: Player) -> None:
    """A rider sits on a horse, not inside it."""
    seat = Seat(host=boat, ride_offset=SADDLE_HEIGHT)
    seat.enter(alice)
    assert alice.position == Coordinates(0.0, 65.0, 0.0)


def test_the_offset_is_kept_as_the_host_moves(boat: Player, alice: Player) -> None:
    seat = Seat(host=boat, ride_offset=SADDLE_HEIGHT)
    seat.enter(alice)
    boat.move_to(THERE)
    seat.settle_occupant()
    assert alice.position == Coordinates(50.0, 65.0, 0.0)


def test_without_an_offset_the_occupant_shares_the_host_position(
    boat: Player, alice: Player
) -> None:
    """What a minecart wants."""
    seat = Seat(host=boat)
    seat.enter(alice)
    assert alice.position == boat.position


# --- a vehicle is seats, not a seat that counts ------------------------------


def test_a_two_seater_is_two_seats(boat: Player, alice: Player, bob: Player) -> None:
    """A boat holds two by owning two seats, leaving each one a simple question."""
    front, back = Seat(host=boat), Seat(host=boat, ride_offset=Coordinates(0.0, 0.0, -1.0))
    assert front.enter(alice) is True
    assert back.enter(bob) is True

    boat.move_to(THERE)
    front.settle_occupant()
    back.settle_occupant()
    assert alice.position == THERE
    assert bob.position == Coordinates(50.0, 64.0, -1.0)


# --- the trait did not have to change ----------------------------------------


def test_seat_adds_nothing_to_the_trait_but_a_position() -> None:
    """The claim the trait was designed around, checked against the real class.

    `Seat` overrides `occupant_position` and nothing else — no entering, no
    leaving, no refusing of its own.
    """
    overridden = set(vars(Seat)) & {
        "enter",
        "exit",
        "can_enter",
        "refusal_reason",
        "settle_occupant",
        "is_occupied",
        "is_occupied_by",
    }
    assert not overridden, f"Seat should not have needed to override {overridden}"


def test_seat_knows_nothing_about_entities() -> None:
    """A host is anything positioned; a seat should not ask what kind."""
    import grimmcraft_core.occupiable.seat as seat_module

    for forbidden in ("CoreEntity", "Player", "Npc", "Mob", "Block"):
        assert not hasattr(seat_module, forbidden), f"seat imported {forbidden}"
