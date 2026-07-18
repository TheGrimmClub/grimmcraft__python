"""The ``grimmcraft-decompile`` command-line interface (click + rich)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import click
from rich.console import Console

# from grimmcraft_compiler.compiler import compile_machines
# from grimmcraft_compiler.target import Flavor, Target
# from grimmcraft_compiler.version import supported_versions


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.option("--version", "mc_version", default="1.21.11", show_default=True,
              help="Target Minecraft version (e.g. 1.21.11).")
#@click.option("--flavor", type=click.Choice([f.value for f in Flavor]),
#              default=Flavor.VANILLA.value, show_default=True,
#              help="Server/loader flavor.")
#@click.option("--namespace", default="grimmcraft", show_default=True,
#              help="Datapack namespace.")
#@click.option("--machine", "machine", type=click.Choice(["all", *_MACHINE_FACTORIES]),
#              default="all", show_default=True, help="Which demo machine(s) to compile.")
#@click.option("--output", "-o", type=click.Path(path_type=Path), default=None,
#              help="Output directory (default: dist/<namespace>).")
#@click.option("--zip", "zip_output", is_flag=True, help="Also produce a .zip.")
#@click.option("--strict", is_flag=True, help="Promote warnings to errors.")
#@click.option("--force", is_flag=True, help="Emit even when errors are present.")
#@click.option("--dry-run", is_flag=True, help="Validate and report; emit nothing.")
@click.option("--no-color", is_flag=True, help="Disable colourised output.")
#@click.option("--list-versions", is_flag=True, help="List supported versions and exit.")
def main(
    mc_version: str,
#    flavor: str,
#    namespace: str,
#    machine: str,
#    output: Path | None,
#    zip_output: bool,
#    strict: bool,
#    force: bool,
#    dry_run: bool,
     no_color: bool,
#    list_versions: bool,
) -> None:
    """Compile grimmcraft state machines into an installable Minecraft datapack."""
    console = Console(no_color=no_color, highlight=False)

    if 0:
      if list_versions:
          console.print("Supported versions: " + ", ".join(supported_versions()))
          raise SystemExit(0)

      try:
          target = Target.resolve(mc_version, flavor)
      except ValueError as exc:
          console.print(f"[bold red]error[/bold red]: {exc}")
          raise SystemExit(2) from None

      machines = _load_machines(machine)

      result = compile_machines(
          machines,
          target,
          namespace=namespace,
          output=output,
          zip_output=zip_output,
          strict=strict,
          force=force,
          dry_run=dry_run,
      )

      result.diagnostics.report(console)

      if result.emitted and result.output_path is not None:
          console.print(
              f"\n[green]✓[/green] Wrote datapack to "
              f"[bold]{result.output_path}[/bold] for {target}."
          )
          console.print(
              "  Install: copy it into [bold]saves/<world>/datapacks/[/bold], "
              "then run [bold]/reload[/bold]."
          )
          console.print(
              f"  See [bold]{result.output_path}/INSTALL.md[/bold] "
              "(or the pack's INSTALL.md) for trigger commands."
          )
      elif dry_run:
          console.print("\n[cyan]dry run[/cyan]: no datapack written.")
      elif result.diagnostics.has_errors:
          console.print(
              "\n[bold red]✗[/bold red] Not emitted due to errors "
              "(use --force to emit anyway)."
          )
    return None
    raise SystemExit(1 if result.diagnostics.has_errors else 0)


if __name__ == "__main__":
    main()
