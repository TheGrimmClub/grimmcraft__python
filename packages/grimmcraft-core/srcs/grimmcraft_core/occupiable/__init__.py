"""Being inside something: the trait, and the things that use it.

:mod:`~grimmcraft_core.occupiable.occupancy` holds the trait itself and imports
nothing but coordinates — that is the point of it, and a test asserts it. The
concrete occupiables live beside it, and between them they cover both halves of
the trait: a :class:`~grimmcraft_core.occupiable.bed.Bed` holds its occupant at a
fixed place, a :class:`~grimmcraft_core.occupiable.seat.Seat` carries theirs
around.

:mod:`~grimmcraft_core.occupiable.vehicle` builds on the seat: a
:class:`~grimmcraft_core.occupiable.vehicle.Vehicle` is an entity that owns seats
and settles them whenever it moves, which is how passengers get carried without
anything in this codebase ticking. A
:class:`~grimmcraft_core.occupiable.vehicle.Boat` has two seats and a
:class:`~grimmcraft_core.occupiable.vehicle.Minecart` one; that is all they
differ by.
"""

from __future__ import annotations

from grimmcraft_core.occupiable.bed import Bed
from grimmcraft_core.occupiable.occupancy import Occupiable, Sleepable
from grimmcraft_core.occupiable.seat import Seat
from grimmcraft_core.occupiable.vehicle import Boat, Minecart, Vehicle

__all__ = [
    "Occupiable",
    "Sleepable",
    "Seat",
    "Bed",
    "Vehicle",
    "Boat",
    "Minecart",
]
