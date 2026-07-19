"""The ``grimmcraft-structure`` command-line interface (click + rich)."""

from __future__ import annotations

from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from grimmcraft_core import BlockPos
from grimmcraft_structures.capture import DEFAULT_SKIP, capture
from grimmcraft_structures.structure import Structure


def _console(no_color: bool) -> Console:
    return Console(no_color=no_color, highlight=False)


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
def main() -> None:
    """Save and restore Minecraft structures (``.nbt`` templates)."""


@main.command("capture")
@click.argument("world", type=click.Path(exists=True, path_type=Path))
@click.option("--from", "corner_a", nargs=3, type=int, required=True,
              metavar="X Y Z", help="One corner of the box (inclusive).")
@click.option("--to", "corner_b", nargs=3, type=int, required=True,
              metavar="X Y Z", help="The opposite corner (inclusive).")
@click.option("--output", "-o", type=click.Path(path_type=Path), required=True,
              help="Where to write the .nbt structure file.")
@click.option("--dimension", default="overworld", show_default=True,
              help="Which dimension to read (overworld, the_nether, the_end).")
@click.option("--include-air", is_flag=True,
              help="Capture the box verbatim instead of dropping air.")
@click.option("--no-color", is_flag=True, help="Disable colourised output.")
def capture_command(
    world: Path,
    corner_a: tuple[int, int, int],
    corner_b: tuple[int, int, int],
    output: Path,
    dimension: str,
    include_air: bool,
    no_color: bool,
) -> None:
    """Capture a box of blocks from a saved WORLD into a structure file."""
    console = _console(no_color)
    structure = capture(
        world,
        BlockPos(*corner_a),
        BlockPos(*corner_b),
        dimension=dimension,
        include_air=include_air,
        skip=() if include_air else DEFAULT_SKIP,
    )
    if not structure.blocks:
        console.print(
            "[yellow]warning[/yellow]: no blocks were read — is the world saved, "
            "and are those coordinates inside a generated chunk?"
        )
    path = structure.write(output)
    console.print(
        f"[green]✓[/green] Captured {len(structure)} block(s) "
        f"({len(structure.palette)} distinct) into [bold]{path}[/bold]."
    )


@main.command("show")
@click.argument("structure_file", type=click.Path(exists=True, path_type=Path))
@click.option("--no-color", is_flag=True, help="Disable colourised output.")
def show_command(structure_file: Path, no_color: bool) -> None:
    """Summarise a .nbt STRUCTURE_FILE: size, palette and block counts."""
    console = _console(no_color)
    structure = Structure.read(structure_file)

    counts: dict[str, int] = {}
    for block in structure:
        counts[str(block.state)] = counts.get(str(block.state), 0) + 1

    x, y, z = structure.size
    console.print(
        f"[bold]{structure_file.name}[/bold] — {x}x{y}x{z} "
        f"({structure.volume} cells, {len(structure)} blocks, "
        f"DataVersion {structure.data_version})"
    )
    table = Table("count", "block state")
    for state, count in sorted(counts.items(), key=lambda kv: -kv[1]):
        table.add_row(str(count), state)
    console.print(table)


if __name__ == "__main__":
    main()
