"""Being inside something: beds now, seats and saddles later.

# Classes:

- `Occupiable`: holds one occupant, with `enter` and `exit`
- `Sleepable`: an occupant lying at a fixed place

# Why this is a trait and not a base class for blocks

Occupancy is orthogonal to everything else a thing might be. A bed is a block, a
point of interest *and* occupiable; a boat is an entity and occupiable; a minecart
is neither a block nor a point of interest. Merging occupancy into any of those
hierarchies would force the other two to inherit something they are not.

So this is a small mixin that any of them can add, and it deliberately knows
nothing about blocks, villagers, professions or claiming. A bed's point-of-interest
logic and its occupancy logic never touch.

# The one design decision worth stating

The difference between a bed and a seat is **where the occupant is**, and nothing
else. Both hold one occupant, both refuse a second, both let them out again.

- a bed puts the occupant at a fixed place and leaves them there;
- a seat puts the occupant wherever the host currently is, and keeps doing so as
  the host moves.

That difference lives in one overridable property, :attr:`occupant_position`, and
one method that acts on it, :meth:`settle_occupant`. :class:`Sleepable` returns a
fixed position. A ``Seat`` would return its host's position and call
:meth:`settle_occupant` as the host moves — no other part of this changes, which
is what "the seat variant drops in without refactoring" has to mean to be worth
claiming.

Occupants are :class:`~grimmcraft_core.entity.core_entity.CoreEntity`, so players
and villagers work identically. Nothing here asks which it is.
"""

from __future__ import annotations

# Includes standard
from grimmclub_standardlib import TYPE_CHECKING, dataclass

# Includes internal
from grimmcraft_core.coordinates import Coordinates

if TYPE_CHECKING:
    from grimmcraft_core.entity.core_entity import CoreEntity


# Classes
@dataclass(kw_only=True)
class Occupiable:
    """Something one entity at a time can be inside.

    Subclasses say *where* the occupant ends up by overriding
    :attr:`occupant_position`, and may add their own conditions by overriding
    :meth:`refusal_reason`.
    """

    occupant: CoreEntity | None = None

    # --- state ---------------------------------------------------------------
    @property
    def is_occupied(self) -> bool:
        """Whether anyone is currently inside."""
        return self.occupant is not None

    def is_occupied_by(self, entity: CoreEntity) -> bool:
        """Whether ``entity`` specifically is the occupant."""
        return self.occupant is entity

    @property
    def occupant_position(self) -> Coordinates | None:
        """Where an occupant is put, or ``None`` to leave them where they are.

        The seam between a bed and a seat. A fixed value makes this a bed; a
        value read from a moving host makes it a seat.
        """
        return None

    # --- entering and leaving ------------------------------------------------
    def refusal_reason(self, entity: CoreEntity) -> str | None:
        """Why ``entity`` may not enter, or ``None`` if they may.

        The base rule is only that there is room. Subclasses add their own —
        a bed refuses in daylight — by overriding this and deferring upwards,
        so every condition is asked in one place and reported the same way.
        """
        if self.occupant is entity:
            return "already inside"
        if self.is_occupied:
            return "occupied"
        return None

    def can_enter(self, entity: CoreEntity) -> bool:
        """Whether ``entity`` could enter right now."""
        return self.refusal_reason(entity) is None

    def enter(self, entity: CoreEntity) -> bool:
        """Put ``entity`` inside. Returns whether it worked.

        A refusal is an ordinary answer, not an error: something else is in the
        bed, or it is daytime. Callers that want the reason ask
        :meth:`refusal_reason` — which is also why the reason exists separately
        rather than being an exception message.
        """
        if not self.can_enter(entity):
            return False
        self.occupant = entity
        self.settle_occupant()
        return True

    def exit(self) -> CoreEntity | None:
        """Let the occupant out and return them, or ``None`` if empty."""
        leaving, self.occupant = self.occupant, None
        return leaving

    def settle_occupant(self) -> None:
        """Move the occupant to :attr:`occupant_position`, if there is one.

        Called on entry, and by a moving host every time it moves. Safe to call
        with nobody inside.
        """
        position = self.occupant_position
        if self.occupant is not None and position is not None:
            self.occupant.teleport(position)


@dataclass(kw_only=True)
class Sleepable(Occupiable):
    """Something an entity lies in, at a fixed place.

    ``rest_position`` is where the occupant is put. Left unset, the occupant
    stays where they were — which is what a sleepable thing that has not been
    placed in the world should do.
    """

    rest_position: Coordinates | None = None

    @property
    def occupant_position(self) -> Coordinates | None:
        """Fixed, unlike a seat's, which follows its host."""
        return self.rest_position

    @property
    def sleeper(self) -> CoreEntity | None:
        """The occupant, under the name that reads correctly for a bed."""
        return self.occupant
