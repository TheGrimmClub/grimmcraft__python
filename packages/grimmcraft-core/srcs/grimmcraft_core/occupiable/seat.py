"""Sitting in something that moves: boats, minecarts and saddled mounts.

# Classes:

- `Seat( host, ride_offset )`: an occupant carried by a moving host

# The other half of the trait

:class:`~grimmcraft_core.occupiable.occupancy.Sleepable` puts its occupant at a
fixed place; a seat puts them wherever its host currently is. That is the whole
difference, and it is why :attr:`occupant_position` exists as an overridable
property — this module changes nothing in ``Occupiable``, which is what
"the seat variant drops in without refactoring" was meant to mean.

# What a host is

Anything :class:`~grimmcraft_core.protocols.Positioned` — it needs a position and
nothing else. A boat and a minecart are entities, a saddled horse is a mob, and a
seat should not have to know which. Keeping the host structural also keeps this
module free of entity imports, exactly as the trait itself is free of block ones.

# Who moves the occupant

Nothing here ticks. ``occupant_position`` is computed from the host every time it
is read, so it is never stale, but the occupant is only *teleported* when
:meth:`~grimmcraft_core.occupiable.occupancy.Occupiable.settle_occupant` is
called. Whoever moves the host calls it. When a ticking or movement-event system
arrives, that call moves there and nothing in this class changes.

# Vehicles with more than one place to sit

A seat holds one occupant, because that is what makes "the seat is taken" a
question with an answer. A boat, which holds two, is a vehicle with a *list* of
seats — not a seat that has learned to count.
"""

from __future__ import annotations

# Includes standard
from grimmclub_standardlib import dataclass

# Includes internal
from grimmcraft_core.coordinates import Coordinates
from grimmcraft_core.occupiable.occupancy import Occupiable
from grimmcraft_core.protocols import Positioned


# Main Class
@dataclass(kw_only=True)
class Seat(Occupiable):
    """A place in or on something that moves, carrying its occupant along.

    ``ride_offset`` is where the occupant sits relative to the host — a rider
    sits above a horse, not inside it. Left unset the occupant shares the host's
    position exactly, which is what a minecart wants.
    """

    host: Positioned
    ride_offset: Coordinates | None = None

    @property
    def occupant_position(self) -> Coordinates:
        """The host's position, offset — read fresh, so it is never stale.

        Fixed for a bed, computed here: the one seam between the two.
        """
        position = self.host.position
        return position if self.ride_offset is None else position + self.ride_offset
