"""grimmcraft-control ``machine`` — a pure, type-safe state-machine controller.

Six primitives compose the whole thing: :class:`State`, :class:`Event`,
:class:`Transition`, :class:`Command`, :class:`Result` and :class:`Machine`
(declared with :class:`MachineBuilder`).  Dispatching an event is
side-effect-free — it returns the :class:`Command`\\ s to run, which a
:class:`CommandBus` executes at the edge.  The compiler consumes the same
declarative structure to emit an ``mcfunction`` datapack.
"""

from __future__ import annotations

from grimmcraft_control.machine.command import Command, CommandBus, CommandHandler
from grimmcraft_control.machine.effects import (
    add_score,
    fill,
    give,
    particle,
    playsound,
    say,
    set_score,
    setblock,
    summon,
    tellraw,
)
from grimmcraft_control.machine.errors import (
    GuardError,
    InvalidTransition,
    MachineBuildError,
    StateMachineError,
)
from grimmcraft_control.machine.event import Event
from grimmcraft_control.machine.machine import (
    STATE_OBJECTIVE,
    TICK_EVENT,
    Machine,
    MachineBuilder,
    StateDraft,
    TransitionDraft,
    new_machine,
)
from grimmcraft_control.machine.result import Result
from grimmcraft_control.machine.state import State
from grimmcraft_control.machine.transition import (
    Action,
    Condition,
    Guard,
    Transition,
)
from grimmcraft_control.machine.vocabulary import CommandName, ConditionName

__all__ = [
    "State",
    "Event",
    "Transition",
    "Condition",
    "Guard",
    "Action",
    "Command",
    "CommandName",
    "ConditionName",
    "CommandHandler",
    "CommandBus",
    "Result",
    "Machine",
    "MachineBuilder",
    "new_machine",
    "StateDraft",
    "TransitionDraft",
    "STATE_OBJECTIVE",
    "TICK_EVENT",
    "StateMachineError",
    "MachineBuildError",
    "InvalidTransition",
    "GuardError",
    # command constructors (grimmcraft_control.machine.effects)
    "setblock",
    "fill",
    "say",
    "tellraw",
    "playsound",
    "particle",
    "summon",
    "give",
    "set_score",
    "add_score",
]
