"""The :class:`Source` base for the *inputs* family — components that originate power.

A source reads no faces (:meth:`inputs` is empty); its output is a function of its
own internal state (a lever's toggle, a button's countdown, a sensor's reading),
which it republishes each tick.  Sources power adjacent dust and strongly power a
solid block they sit against.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence

from grimmcraft_core.coordinates import Direction

from grimmcraft_redstone.component import RedstoneComponent, SignalChange, SimContext
from grimmcraft_redstone.signal import OFF, Signal


class Source(RedstoneComponent):
    """A power source: emits its own signal, reads nothing.

    Subclasses implement :meth:`_desired_output` from their state and call
    :meth:`_refresh` whenever that state changes so the new signal is visible on
    the very next tick.
    """

    EMITS_POWER = True

    def inputs(self) -> Iterable[Direction]:
        """Sources read no input faces."""
        return ()

    def _desired_output(self) -> Signal:
        """The signal this source should currently emit (from its state)."""
        return OFF

    def _refresh(self) -> None:
        """Republish the output immediately after a state change."""
        self._output = self._desired_output()

    def update(self, ctx: SimContext, tick: int) -> Sequence[SignalChange]:
        """Re-evaluate the output from current state (advances any timers)."""
        return self._set_output(self._desired_output())
