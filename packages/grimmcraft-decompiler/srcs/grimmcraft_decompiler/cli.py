"""The ``grimmcraft-decompile`` command-line interface (click + rich)."""

from __future__ import annotations

from pathlib import Path

import click
from rich.console import Console

from grimmcraft_compiler.target import Flavor
from grimmcraft_compiler.version import supported_versions
from grimmcraft_decompiler.decompiler import EMIT_LEVELS, decompile


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.argument(
    "input_path",
    metavar="INPUT",
    type=click.Path(exists=True, path_type=Path),
    required=False,
)
@click.option(
    "--emit",
    type=click.Choice(EMIT_LEVELS),
    default="python",
    show_default=True,
    help="What to reconstruct: the IR, a machine summary, or builder Python.",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    default=None,
    help="Write the result here instead of printing it.",
)
@click.option(
    "--version",
    "mc_version",
    default=None,
    help="Override the auto-detected Minecraft version (e.g. 1.21.11).",
)
@click.option(
    "--flavor",
    type=click.Choice([f.value for f in Flavor]),
    default=Flavor.VANILLA.value,
    show_default=True,
    help="Server/loader flavor, when the pack does not record one.",
)
@click.option("--strict", is_flag=True, help="Promote warnings to errors.")
@click.option("--force", is_flag=True, help="Write output even when errors are present.")
@click.option("--dry-run", is_flag=True, help="Analyse and report; write nothing.")
@click.option(
    "--roundtrip",
    "check_roundtrip",
    is_flag=True,
    help="Recompile the result and report any difference from the original.",
)
@click.option("--no-color", is_flag=True, help="Disable colourised output.")
@click.option(
    "--list-versions", is_flag=True, help="List supported versions and exit."
)
def main(
    input_path: Path | None,
    emit: str,
    output: Path | None,
    mc_version: str | None,
    flavor: str,
    strict: bool,
    force: bool,
    dry_run: bool,
    check_roundtrip: bool,
    no_color: bool,
    list_versions: bool,
) -> None:
    """Lift an installed Minecraft datapack back into the grimmcraft model.

    INPUT is a datapack directory or a .zip archive.
    """
    console = Console(no_color=no_color, highlight=False)

    if list_versions:
        console.print("Supported versions: " + ", ".join(supported_versions()))
        raise SystemExit(0)

    if input_path is None:
        raise click.UsageError("INPUT is required (a datapack directory or .zip)")

    try:
        result = decompile(
            input_path,
            emit=emit,
            version=mc_version,
            flavor=flavor,
            output=output,
            strict=strict,
            force=force,
            dry_run=dry_run,
            check_roundtrip=check_roundtrip,
        )
    except (FileNotFoundError, ValueError) as exc:
        console.print(f"[bold red]error[/bold red]: {exc}")
        raise SystemExit(2) from None

    with result.source:
        _report(console, result, emit=emit, output=output, dry_run=dry_run)
        raise SystemExit(1 if result.diagnostics.has_errors else 0)


def _report(
    console: Console,
    result: object,
    *,
    emit: str,
    output: Path | None,
    dry_run: bool,
) -> None:
    """Print the reconstruction, the diagnostics, and a closing summary."""
    from grimmcraft_decompiler.decompiler import DecompileResult

    assert isinstance(result, DecompileResult)

    if not dry_run and output is None:
        # The reconstruction is the payload — print it unstyled so it can be piped.
        console.print(result.output, markup=False, highlight=False)

    console.print()
    result.diagnostics.report(console)

    if result.diff is not None:
        style = "green" if result.diff.identical else "yellow"
        console.print(f"\n[{style}]{result.diff.render()}[/{style}]")

    if emit in ("machine", "python") and not result.liftable:
        console.print(
            "\n[yellow]note[/yellow]: no grimmcraft machines were found, so the "
            f"IR was printed instead of {emit}."
        )

    if result.output_path is not None:
        console.print(
            f"\n[green]✓[/green] Wrote {emit} to [bold]{result.output_path}[/bold] "
            f"for {result.target}."
        )
    elif dry_run:
        console.print("\n[cyan]dry run[/cyan]: nothing written.")


if __name__ == "__main__":
    main()
