"""The *outputs* family: loads that consume redstone power."""

from __future__ import annotations

from grimmcraft_redstone.outputs.base import Load
from grimmcraft_redstone.outputs.loads import (
    PISTON_PUSH_LIMIT,
    ActivatorRail,
    Bell,
    Dispenser,
    Door,
    Dropper,
    FenceGate,
    Hopper,
    NoteBlock,
    Piston,
    PoweredRail,
    RedstoneLamp,
    StickyPiston,
    Tnt,
    Trapdoor,
)

__all__ = [
    "Load",
    "RedstoneLamp",
    "Piston",
    "StickyPiston",
    "PISTON_PUSH_LIMIT",
    "Dispenser",
    "Dropper",
    "NoteBlock",
    "Bell",
    "Hopper",
    "Door",
    "Trapdoor",
    "FenceGate",
    "Tnt",
    "PoweredRail",
    "ActivatorRail",
]
