#!/usr/bin/env python
"""Decompile every committed example datapack back into builder Python.

The committed ``generated/`` packs are the natural fixtures: each was
produced from a hand-written builder script, so the output here can be read
side by side with the original to see how much survives the trip.

Run it (from the package dir, or via ``task decompiler:example``)::

    uv run --package grimmcraft-decompiler python examples/decompile_examples.py
"""

# Imports
from pathlib import Path

from grimmclub import banner
from grimmcraft_decompiler import decompile

# Constants
EXAMPLES = Path(__file__).resolve().parents[2] / "generated"
OUTPUT = Path("dist/decompiled")


# Code
def decompile_one(pack: Path) -> None:
    """Decompile one datapack and write the reconstructed Python next to it."""
    destination = OUTPUT / f"{pack.name.replace('-', '_')}.py"
    result = decompile(pack, emit="python", output=destination)

    with result.source:
        machines = ", ".join(machine.name for machine in result.machines) or "none"
        print(f"  {pack.name}")
        print(f"    target   : {result.target} ({result.detection.confidence.value})")
        print(f"    machines : {machines}")
        print(f"    written  : {result.output_path}")
        warnings = len(result.diagnostics.warnings)
        if warnings:
            print(f"    warnings : {warnings}")


# Main function
def main() -> None:
    if not EXAMPLES.is_dir():
        print(f"no example packs at {EXAMPLES} — run `task compiler:example` first")
        return

    banner("decompiling the committed example datapacks")
    packs = sorted(p for p in EXAMPLES.iterdir() if p.is_dir() and any(p.iterdir()))
    for pack in packs:
        decompile_one(pack)

    print(f"\nWrote {len(packs)} module(s) to {OUTPUT}/.")
    print("Each one rebuilds its machines and recompiles the datapack it came from.")


# Call main when script is executed
if __name__ == "__main__":
    main()
