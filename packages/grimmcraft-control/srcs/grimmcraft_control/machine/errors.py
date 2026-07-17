"""Exceptions raised while building or driving a :class:`~.machine.Machine`."""

from __future__ import annotations


class StateMachineError(Exception):
    """Base class for every state-machine error."""


class MachineBuildError(StateMachineError):
    """A machine definition is invalid (unknown state, no initial, ambiguity)."""


class InvalidTransition(StateMachineError):
    """A ``strict=True`` machine received an event with no matching transition."""


class GuardError(StateMachineError):
    """A transition guard raised while being evaluated."""
