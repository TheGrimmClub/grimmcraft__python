"""The environment-check example."""

from __future__ import annotations

from grimmcraft_examples.greetings import greet


def test_greet() -> None:
    assert greet("World") == "Hello, World!"


def test_greet_handles_an_empty_name() -> None:
    """Not a validation rule -- just pinning what it does rather than guessing."""
    assert greet("") == "Hello, !"
