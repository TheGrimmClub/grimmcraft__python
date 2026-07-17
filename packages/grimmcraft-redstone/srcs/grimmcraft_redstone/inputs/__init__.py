"""The *inputs* family: components that originate redstone power."""

from __future__ import annotations

from grimmcraft_redstone.inputs.base import Source
from grimmcraft_redstone.inputs.sources import (
    AnalogSource,
    Button,
    DaylightSensor,
    DetectorRail,
    Lectern,
    Lever,
    Observer,
    PressurePlate,
    RedstoneBlock,
    TargetBlock,
    TripwireHook,
    WeightedPressurePlate,
)

__all__ = [
    "Source",
    "Lever",
    "Button",
    "RedstoneBlock",
    "Observer",
    "PressurePlate",
    "WeightedPressurePlate",
    "DaylightSensor",
    "AnalogSource",
    "TargetBlock",
    "Lectern",
    "TripwireHook",
    "DetectorRail",
]
