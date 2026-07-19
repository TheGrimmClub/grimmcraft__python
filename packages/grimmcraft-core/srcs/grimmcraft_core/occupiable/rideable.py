"""Carrying passengers, for anything that can be ridden.

# Classes:

- `Rideable`: owns seats, and settles them whenever it moves

# Why this is a mixin and not the vehicle base

The same argument the trait itself was built on, one level up. A boat is a
vehicle and rideable; a horse is a *mob* and rideable — it has AI, health, drops
and breeding, and the registry files it under "Passive mobs", not "Vehicles".
Folding "carries passengers" into either hierarchy makes the other inherit what
it is not: a `Vehicle` base would give a horse a category it fails, and a `Mob`
base would give a minecart hostility and loot.

So carrying is a mixin over :class:`~grimmcraft_core.occupiable.seat.Seat`, and
:class:`~grimmcraft_core.occupiable.vehicle.Vehicle` and
:class:`~grimmcraft_core.occupiable.mount.Mount` each add it to their own base.

# It has to come first

``class Vehicle(Rideable, CoreEntity)`` — the mixin goes on the left so its
:meth:`move_to` runs before the entity's and can settle the seats afterwards.
Written the other way round the passengers never move.

# What it needs from whoever mixes it in

A ``position``, because that is what its seats are hosted on. Everything here
assumes the concrete class is
:class:`~grimmcraft_core.protocols.Positioned`; both users are entities, which
always are.
"""

# Includes
from __future__ import annotations

# Includes standard
from grimmclub_standardlib import TYPE_CHECKING, ClassVar, dataclass, field

# Includes internal
from grimmcraft_core.coordinates import Coordinates
from grimmcraft_core.occupiable.seat import Seat

if TYPE_CHECKING:
    from grimmcraft_core.entity.core_entity import CoreEntity

# Constants
#: A seat at the host's own position.
NO_OFFSET = Coordinates(0.0, 0.0, 0.0)


# Classes
@dataclass(kw_only=True)
class Rideable:
    """Something with seats, that brings its passengers along when it moves.

    Seats are built from :attr:`seat_offsets` and are not a constructor
    argument: accepting a list of seats would let one be built with seats hosted
    by something else, or with a number that contradicts its kind.
    """

    if TYPE_CHECKING:
        # Declared for the type checker only. `Rideable` is always mixed into
        # something Positioned — that is what its seats are hosted on — but the
        # position belongs to the concrete class, not here. Under TYPE_CHECKING
        # this block never runs, so no dataclass field is created and no
        # subclass has to redeclare it.
        position: Coordinates

    #: Where each seat is, relative to the host. The length is the seat count.
    seat_offsets: ClassVar[tuple[Coordinates, ...]] = (NO_OFFSET,)

    seats: list[Seat] = field(init=False)

    def __post_init__(self) -> None:
        # Cooperative: whatever this is mixed into may have its own validation
        # (an entity clamps health), and it has to run before the seats are
        # built on top of it. Guarded because the mixin must also work alone.
        parent_post_init = getattr(super(), "__post_init__", None)
        if parent_post_init is not None:
            parent_post_init()
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
    def boarding_refusal_reason(self, entity: CoreEntity) -> str | None:
        """Why ``entity`` may not get on, or ``None`` if they may.

        The base rules are that they are not already aboard and that there is a
        free seat. Subclasses add their own — a mount refuses without a saddle —
        by overriding this and deferring upwards, exactly as
        :meth:`~grimmcraft_core.occupiable.occupancy.Occupiable.refusal_reason`
        does one level down.

        Kept here rather than on the seat because these are questions about the
        *whole* thing: a seat knows only whether it is taken, and would happily
        accept a passenger already sitting in the seat behind.
        """
        if self.is_carrying(entity):
            return "already aboard"
        if self.is_full:
            return "full"
        return None

    def can_board(self, entity: CoreEntity) -> bool:
        """Whether ``entity`` could get on right now."""
        return self.boarding_refusal_reason(entity) is None

    def board(self, entity: CoreEntity) -> bool:
        """Put ``entity`` in the first free seat. Returns whether it worked.

        A refusal is an ordinary answer, as everywhere else in this package;
        :meth:`boarding_refusal_reason` supplies the why.
        """
        if not self.can_board(entity):
            return False
        return any(seat.enter(entity) for seat in self.seats)

    def disembark(self, entity: CoreEntity) -> bool:
        """Take ``entity`` out of whichever seat holds them.

        Returns whether they were aboard. Where they go next is not our
        business, the same as getting out of a bed.
        """
        seat = self.seat_of(entity)
        if seat is None:
            return False
        # `exit` hands back the occupant; the answer here is whether they were
        # aboard, not who they were. Returning the entity would make an empty
        # seat and a successful disembark both falsy.
        seat.exit()
        return True

    def eject_all(self) -> list[CoreEntity]:
        """Empty every seat and return who was in them, in seating order."""
        leaving = self.passengers
        for seat in self.seats:
            _ = seat.exit()
        return leaving

    # --- carrying them --------------------------------------------------------
    def carry_passengers(self) -> None:
        """Bring every passenger to their seat. Safe with nobody aboard."""
        for seat in self.seats:
            seat.settle_occupant()

    def move_to(self, position: Coordinates) -> None:
        """Move, bringing the passengers along — the point of being rideable."""
        super().move_to(position)  # type: ignore[misc]
        self.carry_passengers()

    def teleport(self, position: Coordinates) -> None:
        """Instantly relocate, passengers included."""
        super().teleport(position)  # type: ignore[misc]
        self.carry_passengers()
