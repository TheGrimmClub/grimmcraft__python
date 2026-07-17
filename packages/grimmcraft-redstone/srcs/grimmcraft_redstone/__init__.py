"""grimmcraft-redstone — a simulatable model of Minecraft redstone.

Redstone is modelled as a spatial graph of :class:`~grimmcraft_redstone.component.RedstoneComponent`
placed in a :class:`~grimmcraft_redstone.circuit.Circuit` and driven by a
tick-based :class:`~grimmcraft_redstone.simulation.Simulator`.  Components fall
into four families — **inputs** (sources), **connectors** (transmission),
**outputs** (loads) and **functions** (logic) — and pass around a
:class:`~grimmcraft_redstone.signal.Signal` (power 0-15, strong/weak).

The most-used names are re-exported here; the families live in the
``inputs`` / ``connectors`` / ``outputs`` / ``functions`` sub-packages.
"""

from __future__ import annotations

from grimmcraft_redstone.circuit import Circuit
from grimmcraft_redstone.component import (
    Conductor,
    Load,
    LogicGate,
    PowerSource,
    RedstoneComponent,
    SignalChange,
    SimContext,
)
from grimmcraft_redstone.connectors import RedstoneDust, SolidBlock
from grimmcraft_redstone.diagnostics import (
    Codes,
    Diagnostic,
    DiagnosticBag,
    Severity,
    analyze,
)
from grimmcraft_redstone.functions import (
    AndGate,
    Clock,
    Comparator,
    ComparatorMode,
    Container,
    NandGate,
    NotGate,
    OrGate,
    RedstoneTorch,
    Repeater,
    XorGate,
)
from grimmcraft_redstone.inputs import (
    Button,
    DaylightSensor,
    Lever,
    Observer,
    PressurePlate,
    RedstoneBlock,
    Source,
    WeightedPressurePlate,
)
from grimmcraft_redstone.outputs import (
    Dispenser,
    Door,
    Hopper,
    NoteBlock,
    Piston,
    RedstoneLamp,
    StickyPiston,
    Tnt,
)
from grimmcraft_redstone.signal import (
    GAME_TICKS_PER_REDSTONE_TICK,
    MAX_POWER,
    OFF,
    PowerKind,
    Signal,
    redstone_ticks,
)
from grimmcraft_redstone.simulation import (
    Simulator,
    StabilizeResult,
    StepResult,
    dust_field,
)

__all__ = [
    # signal
    "Signal",
    "PowerKind",
    "OFF",
    "MAX_POWER",
    "GAME_TICKS_PER_REDSTONE_TICK",
    "redstone_ticks",
    # graph + engine
    "Circuit",
    "Simulator",
    "StepResult",
    "StabilizeResult",
    "dust_field",
    # base + protocols
    "RedstoneComponent",
    "SignalChange",
    "SimContext",
    "PowerSource",
    "Conductor",
    "Load",
    "LogicGate",
    # inputs
    "Source",
    "Lever",
    "Button",
    "RedstoneBlock",
    "Observer",
    "PressurePlate",
    "WeightedPressurePlate",
    "DaylightSensor",
    # connectors
    "RedstoneDust",
    "SolidBlock",
    # outputs
    "RedstoneLamp",
    "Piston",
    "StickyPiston",
    "Dispenser",
    "Door",
    "Hopper",
    "NoteBlock",
    "Tnt",
    # functions
    "RedstoneTorch",
    "Repeater",
    "Comparator",
    "ComparatorMode",
    "Container",
    "NotGate",
    "AndGate",
    "OrGate",
    "NandGate",
    "XorGate",
    "Clock",
    # diagnostics
    "analyze",
    "Diagnostic",
    "DiagnosticBag",
    "Severity",
    "Codes",
]
