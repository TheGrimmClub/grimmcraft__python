"""Being inside something: the trait, and the things that use it.

:mod:`~grimmcraft_core.occupiable.occupancy` holds the trait itself and imports
nothing but coordinates — that is the point of it, and a test asserts it. The
concrete occupiables live beside it, and between them they cover both halves of
the trait: a :class:`~grimmcraft_core.occupiable.bed.Bed` holds its occupant at a
fixed place, a :class:`~grimmcraft_core.occupiable.seat.Seat` carries theirs
around. A boat or a minecart is a vehicle owning seats, and would go here too.
"""

from __future__ import annotations

from grimmcraft_core.occupiable.bed import Bed
from grimmcraft_core.occupiable.occupancy import Occupiable, Sleepable
from grimmcraft_core.occupiable.seat import Seat

__all__ = [
    "Occupiable",
    "Sleepable",
    "Seat",
    "Bed",
]
