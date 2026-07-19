"""The smallest possible example: one function, importable from another package.

Kept because it is the first thing a trainee runs to check their environment
works -- if ``greet`` imports, the workspace is installed correctly. It lived in
``grimmcraft-core`` originally, which put a hello-world in the domain model.

# Functions:

- `greet(name)`: a friendly greeting
"""

from __future__ import annotations


def greet(name: str) -> str:
    """Return a friendly greeting for ``name``."""
    return f"Hello, {name}!"
