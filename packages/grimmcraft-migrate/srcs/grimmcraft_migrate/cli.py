"""The ``grimmcraft-migrate`` command line: ``classify``, ``migrate``, ``verify``.

Built on :mod:`argparse` rather than ``click`` so this package keeps its
standard-library-only promise and can be lifted out and run anywhere.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from grimmcraft_migrate.classify import classify_inventory
from grimmcraft_migrate.inventory import Inventory, read_inventory
from grimmcraft_migrate.migrate import CommandMigrator
from grimmcraft_migrate.report import MigrationReport
from grimmcraft_migrate.verify import build_verification_pack


def _run_classify(arguments: argparse.Namespace) -> int:
    inventory = read_inventory(arguments.input)
    report = classify_inventory(inventory)
    text = report.to_markdown()

    if arguments.output:
        Path(arguments.output).write_text(text, encoding="utf-8")
        print(f"Wrote classification report to {arguments.output}")
    else:
        print(text)

    if report.needed_flags:
        print(
            f"\n{len(report.needed_flags)} legacy pattern(s) found: "
            + ", ".join(report.needed_flags),
            file=sys.stderr,
        )
    return 0


def _run_migrate(arguments: argparse.Namespace) -> int:
    inventory = read_inventory(arguments.input)
    migrator = CommandMigrator()
    report = MigrationReport()
    migrated_entries = []

    for entry in inventory:
        result = migrator.migrate_command(entry.command)
        report.add(entry, result)
        migrated = type(entry)(
            command=result.migrated,
            dimension=entry.dimension,
            x=entry.x,
            y=entry.y,
            z=entry.z,
            extra=entry.extra,
        )
        migrated_entries.append(migrated)

    Inventory(entries=migrated_entries, format=inventory.format).write(
        arguments.output
    )
    Path(arguments.report).write_text(report.to_markdown(), encoding="utf-8")

    print(
        f"Migrated {len(report.changed)} of {len(report.results)} command(s) "
        f"→ {arguments.output}"
    )
    print(f"Report → {arguments.report}")
    if report.failed:
        print(
            f"\n{len(report.failed)} command(s) could not be migrated and were "
            "left unchanged; see the report.",
            file=sys.stderr,
        )
        return 1
    return 0


def _run_verify(arguments: argparse.Namespace) -> int:
    inventory = read_inventory(arguments.input)
    root = build_verification_pack(
        list(inventory), arguments.output, namespace=arguments.namespace
    )
    print(f"Wrote verification datapack to {root}")
    print("Copy it into saves/<world>/datapacks/ and /reload in a 1.21 instance.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="grimmcraft-migrate",
        description=(
            "Migrate Minecraft command strings from 1.19 syntax to 1.21 syntax."
        ),
    )
    subcommands = parser.add_subparsers(dest="subcommand", required=True)

    classify = subcommands.add_parser(
        "classify",
        help="Report what the inventory contains, before changing anything.",
    )
    classify.add_argument("input", help="the command inventory (text or JSON)")
    classify.add_argument(
        "--output", "-o", default=None, help="write the report here instead of stdout"
    )
    classify.set_defaults(handler=_run_classify)

    migrate = subcommands.add_parser(
        "migrate", help="Rewrite the inventory into 1.21 syntax."
    )
    migrate.add_argument("input", help="the command inventory (text or JSON)")
    migrate.add_argument(
        "--output", "-o", required=True, help="where to write the migrated inventory"
    )
    migrate.add_argument(
        "--report",
        "-r",
        default="migration-report.md",
        help="where to write the Markdown report",
    )
    migrate.set_defaults(handler=_run_migrate)

    verify = subcommands.add_parser(
        "verify",
        help="Build a datapack of the commands so Minecraft validates them.",
    )
    verify.add_argument("input", help="the migrated command inventory")
    verify.add_argument(
        "--output", "-o", required=True, help="where to write the datapack"
    )
    verify.add_argument(
        "--namespace", default="migration_check", help="datapack namespace"
    )
    verify.set_defaults(handler=_run_verify)

    return parser


def main(argv: list[str] | None = None) -> int:
    """Entry point; returns the process exit code."""
    parser = build_parser()
    arguments = parser.parse_args(argv)
    try:
        exit_code: int = arguments.handler(arguments)
    except (OSError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
