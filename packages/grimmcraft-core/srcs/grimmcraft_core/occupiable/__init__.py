"""Being inside something: the trait, and the things that use it.

:mod:`~grimmcraft_core.occupiable.occupancy` holds the trait itself and imports
nothing but coordinates — that is the point of it, and a test asserts it. The
concrete occupiables live beside it: :mod:`~grimmcraft_core.occupiable.bed` is
the first, and a seat or a boat would be the next.
"""

from __future__ import annotations

from grimmcraft_core.occupiable.bed import Bed
from grimmcraft_core.occupiable.occupancy import Occupiable, Sleepable

__all__ = [
    "Occupiable",
    "Sleepable",
    "Bed",
]
