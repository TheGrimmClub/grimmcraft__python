"""grimmcraft-control — a pure, type-safe state-machine controller.

The controller lives in the :mod:`grimmcraft_control.machine` subpackage; its
public API is re-exported here for convenience.  Ready-made example machines
(door, furnace) live in :mod:`grimmcraft_control.demos`.
"""

from __future__ import annotations

from grimmcraft_control.machine import (
    STATE_OBJECTIVE,
    TICK_EVENT,
    Action,
    Command,
    CommandBus,
    CommandHandler,
    Condition,
    Event,
    Guard,
    GuardError,
    InvalidTransition,
    Machine,
    MachineBuilder,
    MachineBuildError,
    Result,
    State,
    StateMachineError,
    Transition,
)

__all__ = [
    "State",
    "Event",
    "Transition",
    "Condition",
    "Guard",
    "Action",
    "Command",
    "CommandHandler",
    "CommandBus",
    "Result",
    "Machine",
    "MachineBuilder",
    "STATE_OBJECTIVE",
    "TICK_EVENT",
    "StateMachineError",
    "MachineBuildError",
    "InvalidTransition",
    "GuardError",
]
