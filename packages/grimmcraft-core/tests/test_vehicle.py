"""Vehicles: entities that own seats and carry whoever is in them."""

from __future__ import annotations

import pytest

from grimmcraft_core.coordinates import Coordinates
from grimmcraft_core.entity.npc import Npc
from grimmcraft_core.entity.player import Player
from grimmcraft_core.occupiable.vehicle import Boat, Minecart, Vehicle
from grimmcraft_data.entity import Entity

HERE = Coordinates(0.0, 64.0, 0.0)
THERE = Coordinates(50.0, 64.0, 0.0)
BEHIND = Coordinates(0.0, 64.0, -1.0)


@pytest.fixture
def alice() -> Player:
    return Player(position=HERE, name="alice")


@pytest.fixture
def bob() -> Player:
    return Player(position=HERE, name="bob")


@pytest.fixture
def carol() -> Player:
    return Player(position=HERE, name="carol")


@pytest.fixture
def villager() -> Npc:
    return Npc(position=HERE, name="Marlene")


@pytest.fixture
def boat() -> Boat:
    return Boat(position=HERE)


@pytest.fixture
def minecart() -> Minecart:
    return Minecart(position=HERE)


# --- seating plans -----------------------------------------------------------


def test_a_boat_has_two_seats(boat: Boat) -> None:
    assert len(boat.seats) == 2


def test_a_minecart_has_one(minecart: Minecart) -> None:
    assert len(minecart.seats) == 1


def test_the_seats_are_hosted_by_the_vehicle_itself(boat: Boat) -> None:
    """A vehicle is its own seats' host, which is how it knows when to settle."""
    assert all(seat.host is boat for seat in boat.seats)


def test_seat_count_belongs_to_the_kind_not_the_instance() -> None:
    """No boat holds three, so it is a ClassVar rather than a constructor argument."""
    assert Boat(position=HERE).seats != Boat(position=THERE).seats
    assert len(Boat(position=HERE).seats) == len(Boat(position=THERE).seats) == 2


# --- boarding ----------------------------------------------------------------


def test_boarding_takes_the_first_free_seat(boat: Boat, alice: Player, bob: Player) -> None:
    assert boat.board(alice) is True
    assert boat.seats[0].is_occupied_by(alice)
    assert boat.board(bob) is True
    assert boat.seats[1].is_occupied_by(bob)


def test_a_full_boat_refuses(boat: Boat, alice: Player, bob: Player, carol: Player) -> None:
    boat.board(alice)
    boat.board(bob)
    assert boat.is_full
    assert boat.board(carol) is False


def test_a_minecart_holds_one(minecart: Minecart, alice: Player, bob: Player) -> None:
    assert minecart.board(alice) is True
    assert minecart.board(bob) is False


def test_boarding_twice_does_not_take_a_second_seat(boat: Boat, alice: Player) -> None:
    """A seat alone cannot catch this — it only knows whether *it* is taken."""
    assert boat.board(alice) is True
    assert boat.board(alice) is False
    assert boat.passengers == [alice], "not sitting in both seats"


def test_a_villager_can_be_a_passenger(boat: Boat, villager: Npc) -> None:
    """Nothing here asks what kind of entity is aboard."""
    assert boat.board(villager) is True
    assert boat.is_carrying(villager)


def test_an_empty_boat_knows_it(boat: Boat, alice: Player) -> None:
    assert boat.is_empty
    boat.board(alice)
    assert not boat.is_empty


# --- getting off -------------------------------------------------------------


def test_disembarking_frees_the_seat(boat: Boat, alice: Player, bob: Player) -> None:
    boat.board(alice)
    assert boat.disembark(alice) is True
    assert not boat.is_carrying(alice)
    assert boat.board(bob) is True


def test_disembarking_someone_who_is_not_aboard(boat: Boat, alice: Player) -> None:
    assert boat.disembark(alice) is False


def test_ejecting_everyone(boat: Boat, alice: Player, bob: Player) -> None:
    boat.board(alice)
    boat.board(bob)
    assert boat.eject_all() == [alice, bob], "in seating order"
    assert boat.is_empty


def test_the_seat_of_a_passenger(boat: Boat, alice: Player, bob: Player) -> None:
    boat.board(alice)
    boat.board(bob)
    assert boat.seat_of(bob) is boat.seats[1]
    assert boat.seat_of(Player(position=HERE, name="nobody")) is None


# --- carrying ----------------------------------------------------------------


def test_a_moving_vehicle_carries_its_passengers(boat: Boat, alice: Player, bob: Player) -> None:
    """The whole point of a vehicle: no scheduler exists, so moving is the event."""
    boat.board(alice)
    boat.board(bob)
    boat.move_to(THERE)
    assert alice.position == THERE
    assert bob.position == Coordinates(50.0, 64.0, -1.0)


def test_teleporting_carries_them_too(boat: Boat, alice: Player) -> None:
    boat.board(alice)
    boat.teleport(THERE)
    assert alice.position == THERE


def test_boarding_brings_the_passenger_to_the_vehicle(boat: Boat, alice: Player) -> None:
    alice.teleport(Coordinates(-99.0, 10.0, -99.0))
    boat.board(alice)
    assert alice.position == HERE


def test_the_second_seat_sits_behind_the_first(boat: Boat, alice: Player, bob: Player) -> None:
    """Otherwise a two-seater is just two people in the same place."""
    boat.board(alice)
    boat.board(bob)
    assert alice.position == HERE
    assert bob.position == BEHIND


def test_a_minecart_passenger_sits_at_the_cart(minecart: Minecart, alice: Player) -> None:
    minecart.board(alice)
    minecart.move_to(THERE)
    assert alice.position == THERE


def test_moving_an_empty_vehicle_is_safe(boat: Boat) -> None:
    boat.move_to(THERE)  # must not raise
    assert boat.position == THERE


def test_someone_who_got_off_is_no_longer_carried(boat: Boat, alice: Player) -> None:
    boat.board(alice)
    boat.disembark(alice)
    boat.move_to(THERE)
    assert alice.position == HERE, "left where they got out"


# --- the vehicle agrees with the registry ------------------------------------


def test_a_vehicle_must_be_a_vehicle_in_the_data() -> None:
    """Checked against `Entity.category` rather than declared, as Mob does."""
    with pytest.raises(ValueError, match="not a vehicle"):
        Vehicle(entity_type=Entity.ZOMBIE, position=HERE)


def test_the_registry_kinds_are_accepted() -> None:
    assert Boat(position=HERE).entity_type.category == "Vehicles"
    assert Minecart(position=HERE).entity_type.category == "Vehicles"


def test_another_boat_kind_still_works() -> None:
    """A chest boat is a boat; the seating plan is the class's, not the id's."""
    chest_boat = Boat(entity_type=Entity.OAK_CHEST_BOAT, position=HERE)
    assert len(chest_boat.seats) == 2


# --- a vehicle is an entity like any other -----------------------------------


def test_a_vehicle_is_an_entity(boat: Boat) -> None:
    from grimmcraft_core.entity.core_entity import CoreEntity

    assert isinstance(boat, CoreEntity)


def test_a_vehicle_can_be_a_passenger(boat: Boat, minecart: Minecart) -> None:
    """A boat in a minecart is absurd, but nothing should have to forbid it."""
    assert minecart.board(boat) is True
    minecart.move_to(THERE)
    assert boat.position == THERE


def test_carrying_nests_all_the_way_down(boat: Boat, minecart: Minecart, alice: Player) -> None:
    """Nobody wrote this: it falls out of a vehicle being an ordinary occupant.

    Moving the cart settles its seat, which teleports the boat, which is a
    vehicle and so settles its own seats in turn.
    """
    boat.board(alice)
    minecart.board(boat)
    minecart.move_to(THERE)

    assert minecart.position == THERE
    assert boat.position == THERE
    assert alice.position == THERE, "carried two levels up"
