"""The bed: a placeable block you can sleep in.

# Classes:

- `Bed( clock )`: a placed block holding one sleeper, and only at night

# What a bed is made of

A bed is a block *and* occupiable, and those two facts are kept apart exactly as
:mod:`~grimmcraft_core.occupiable.occupancy` argued they should be. Placement,
breaking and being carried come from
:class:`~grimmcraft_core.item.storage.PlaceableBlock`; holding a sleeper comes
from :class:`~grimmcraft_core.occupiable.occupancy.Sleepable`. This module is the
only place that knows a bed is both, which is why it sits beside the trait rather
than among the items.

# Where the sleeper goes

:class:`Sleepable` carries its own ``rest_position``, but a bed already knows
where it is: the ``position`` it was placed at. Keeping both would let them
disagree — a bed placed here that puts its sleeper there — so
:attr:`occupant_position` reads the placement, and ``rest_position`` goes unused.
An unplaced bed has no position, which is exactly the case ``Sleepable`` already
handles by leaving the occupant where they are; here it is refused outright,
since a bed in your pocket is not somewhere to sleep.

# What is deliberately not here

Beds are also points of interest: they decide village population, they are
claimed by a villager as a home, they set a player's respawn point, and enough
players in them skip the night. None of those exist yet — there is no
`PointOfInterest`, no claiming and no respawn — and none of them are needed to
hold a sleeper. When they arrive they attach to a bed from outside, the same way
occupancy does, rather than being folded in here.
"""

from __future__ import annotations

# Includes standard
from grimmclub_standardlib import TYPE_CHECKING, dataclass

# Includes internal
from grimmcraft_core.clock import MinecraftClock, TimeOfDay
from grimmcraft_core.coordinates import Coordinates
from grimmcraft_core.item.storage import PlaceableBlock
from grimmcraft_core.occupiable.occupancy import Sleepable
from grimmcraft_data.item import Item

if TYPE_CHECKING:
    from grimmcraft_core.entity.core_entity import CoreEntity

# Constants
#: Sleeping is allowed from sunset until sunrise, read from the clock's own table
#: of named moments so the two cannot drift apart.
_SUNRISE_HOUR = TimeOfDay.SUNRISE.time[0]
_SUNSET_HOUR = TimeOfDay.SUNSET.time[0]


# Main Class
@dataclass(kw_only=True)
class Bed(PlaceableBlock, Sleepable):
    """A bed: one sleeper at a time, once it is placed and after dark.

    ``clock`` is the world's time. Left unset the bed has no idea what hour it
    is and so does not refuse on those grounds — a bed under test, or one in a
    world without a day/night cycle, still works as a thing you can lie in.
    """

    item_type: Item = Item.RED_BED
    clock: MinecraftClock | None = None

    # --- where the sleeper goes ----------------------------------------------
    @property
    def occupant_position(self) -> Coordinates | None:
        """The bed's own placement, so the two cannot disagree."""
        return self.position

    # --- when you may sleep ---------------------------------------------------
    @property
    def is_night(self) -> bool:
        """Whether it is late enough to sleep. True when the hour is unknown.

        Night wraps midnight, so this is an ``or`` where the daytime test would
        be an ``and``.
        """
        if self.clock is None:
            return True
        hour = self.clock.hour
        return hour >= _SUNSET_HOUR or hour < _SUNRISE_HOUR

    def refusal_reason(self, entity: CoreEntity) -> str | None:
        """Why ``entity`` may not sleep here, or ``None`` if they may.

        Defers upwards first, so "occupied" and "already inside" keep their
        wording and stay in one place, then adds the two a bed owns.
        """
        occupancy_refusal = super().refusal_reason(entity)
        if occupancy_refusal is not None:
            return occupancy_refusal
        if not self.is_placed:
            return "not placed"
        if not self.is_night:
            return "it is daytime"
        return None

    # --- interacting ----------------------------------------------------------
    def interact(self, actor: CoreEntity) -> None:
        """Right-clicking a bed is trying to sleep in it.

        ``Interactable`` returns nothing, so a caller who wants to know whether
        it worked calls :meth:`enter` — or :meth:`refusal_reason` for the why.
        """
        self.last_opened_by = actor
        self.enter(actor)

    def break_block(self) -> None:
        """Take the bed back, turfing out whoever is in it.

        Breaking the bed someone is sleeping in cannot leave them registered as
        its occupant, or the broken bed would go on refusing everyone else.
        """
        self.exit()
        super().break_block()
