"""Entry point for the ``grimm`` command.

Still a scaffold: it greets someone. The two PROMPT__*.md files beside this one
describe what it is meant to become.

The greeting is defined here rather than imported. It used to come from
``grimmcraft_core``, which meant the domain model carried a hello-world to keep
a placeholder CLI working; the example now lives in ``grimmcraft-examples``,
which depends on this package rather than the other way round.
"""

from __future__ import annotations

# Includes standard
import argparse


# Functions
def greet(name: str) -> str:
    """Return a friendly greeting for ``name``."""
    return f"Hello, {name}!"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="grimmcraft", description="Greet someone.")
    parser.add_argument("name", nargs="?", default="World", help="who to greet")
    args = parser.parse_args(argv)

    print(greet(args.name))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
