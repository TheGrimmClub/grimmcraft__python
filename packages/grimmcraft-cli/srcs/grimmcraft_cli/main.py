"""Entry point for the ``grimm`` command."""

import argparse

from grimmcraft_core import greet


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="grimmcraft", description="Greet someone.")
    parser.add_argument("name", nargs="?", default="World", help="who to greet")
    args = parser.parse_args(argv)

    print(greet(args.name))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
