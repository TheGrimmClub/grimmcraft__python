"""Things you ride: the vehicle base, and the two that differ only by seating.

# Classes:

- `Vehicle`: an entity that owns seats and carries whoever is in them
- `Boat`: two seats, one behind the other
- `Minecart`: one seat, at the cart

# What a vehicle adds to a seat

A :class:`~grimmcraft_core.occupiable.seat.Seat` knows how to compute where its
occupant belongs, but not *when* to put them there — nothing in this codebase
ticks, so something has to say "I have moved". A vehicle is the thing that can:
it is the host, so it knows the moment its own position changes. Overriding
:meth:`move_to` and :meth:`teleport` to settle its seats is the whole of it, and
it means passengers are carried without any scheduler existing.

That is also the honest boundary of it. A vehicle carries its passengers when
*it* is asked to move. Nothing here makes a minecart roll down a rail on its own.

# Why the seat count is a class attribute

A boat holds two and a minecart holds one, and no boat holds three — the number
belongs to the *kind* of vehicle, not to the instance, so it is a
:data:`~typing.ClassVar` of offsets rather than a constructor argument. Declaring
the offsets rather than the count is what makes it one declaration instead of
two: the length is the seat count, and the values are where the seats are.

Subclassing is therefore all a new vehicle needs. A chest boat is a boat with
storage; a horse would be a mob with one seat.

# Boarding, not entering

:meth:`board` picks the first free seat, so callers do not have to know the
seating plan. It also refuses anyone already aboard, which a seat cannot do on
its own: a seat only knows about itself, and would happily take a passenger who
is already sitting in the seat behind.
"""

from __future__ import annotations

# Includes standard
from grimmclub_standardlib import ClassVar, dataclass, field

# Includes internal
from grimmcraft_core.coordinates import Coordinates
from grimmcraft_core.entity.core_entity import CoreEntity
from grimmcraft_core.occupiable.seat import Seat
from grimmcraft_data.entity import Entity

# Constants
#: The ``Entity.category`` the registry gives boats, minecarts and the rest.
#: Checked rather than declared, so a vehicle cannot disagree with the data.
VEHICLE_CATEGORY = "Vehicles"

#: A seat at the vehicle's own position.
NO_OFFSET = Coordinates(0.0, 0.0, 0.0)


# Functions
def _entity_category(entity_type: Entity) -> str | None:
    """The ``category`` of a data ``Entity`` (dynamically attached attr)."""
    return getattr(entity_type, "category", None)


# Classes
@dataclass(kw_only=True)
class Vehicle(CoreEntity):
    """An entity that carries passengers in seats.

    Seats are built from :attr:`seat_offsets` and are not a constructor
    argument: accepting a list of seats would let a vehicle be built with seats
    hosted by something else, or with a number that contradicts its kind.
    """

    #: Where each seat is, relative to the vehicle. The length is the seat count.
    seat_offsets: ClassVar[tuple[Coordinates, ...]] = (NO_OFFSET,)

    seats: list[Seat] = field(init=False)

    def __post_init__(self) -> None:
        super().__post_init__()
        category = _entity_category(self.entity_type)
        if category is not None and category != VEHICLE_CATEGORY:
            raise ValueError(f"{self.entity_type.name} is not a vehicle (category={category!r})")
        self.seats = [Seat(host=self, ride_offset=offset) for offset in self.seat_offsets]

    # --- who is aboard --------------------------------------------------------
    @property
    def passengers(self) -> list[CoreEntity]:
        """Everyone aboard, in seating order."""
        return [seat.occupant for seat in self.seats if seat.occupant is not None]

    @property
    def is_empty(self) -> bool:
        """Whether nobody is aboard."""
        return not self.passengers

    @property
    def is_full(self) -> bool:
        """Whether every seat is taken."""
        return all(seat.is_occupied for seat in self.seats)

    def is_carrying(self, entity: CoreEntity) -> bool:
        """Whether ``entity`` is in any of the seats."""
        return any(seat.is_occupied_by(entity) for seat in self.seats)

    def seat_of(self, entity: CoreEntity) -> Seat | None:
        """The seat ``entity`` is in, or ``None`` if they are not aboard."""
        return next((seat for seat in self.seats if seat.is_occupied_by(entity)), None)

    # --- getting on and off ---------------------------------------------------
    def board(self, entity: CoreEntity) -> bool:
        """Put ``entity`` in the first free seat. Returns whether it worked.

        Refuses anyone already aboard. A seat alone cannot catch that — it knows
        only whether *it* is taken — so a passenger in the front seat would
        otherwise be accepted into the back one as well.
        """
        if self.is_carrying(entity):
            return False
        return any(seat.enter(entity) for seat in self.seats)

    def disembark(self, entity: CoreEntity) -> bool:
        """Take ``entity`` out of whichever seat holds them.

        Returns whether they were aboard. Where they go next is not the
        vehicle's business, the same as getting out of a bed.
        """
        seat = self.seat_of(entity)
        if seat is None:
            return False
        seat.exit()
        return True

    def eject_all(self) -> list[CoreEntity]:
        """Empty every seat and return who was in them, in seating order."""
        leaving = self.passengers
        for seat in self.seats:
            seat.exit()
        return leaving

    # --- carrying them --------------------------------------------------------
    def carry_passengers(self) -> None:
        """Bring every passenger to their seat. Safe with nobody aboard."""
        for seat in self.seats:
            seat.settle_occupant()

    def move_to(self, position: Coordinates) -> None:
        """Move, bringing the passengers along — the point of being a vehicle."""
        super().move_to(position)
        self.carry_passengers()

    def teleport(self, position: Coordinates) -> None:
        """Instantly relocate, passengers included."""
        super().teleport(position)
        self.carry_passengers()


@dataclass(kw_only=True)
class Boat(Vehicle):
    """A boat: two seats, one behind the other.

    The second passenger sits one block back (``-Z`` is north), which is what
    makes a boat a two-seater rather than two people in the same place.
    """

    seat_offsets: ClassVar[tuple[Coordinates, ...]] = (
        NO_OFFSET,
        Coordinates(0.0, 0.0, -1.0),
    )

    entity_type: Entity = Entity.OAK_BOAT


@dataclass(kw_only=True)
class Minecart(Vehicle):
    """A minecart: one seat, at the cart itself.

    Inherits :attr:`~Vehicle.seat_offsets` unchanged — a single seat at no
    offset is already the default, and restating it here would be a second place
    for it to be wrong.
    """

    entity_type: Entity = Entity.MINECART
