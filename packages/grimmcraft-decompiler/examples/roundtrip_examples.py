#!/usr/bin/env python
"""Decompile then recompile every example pack and prove the bytes match.

This is the round-trip contract as an executable demonstration: for each pack,
lift it to machines, lower those back through the *real* compiler, and diff the
emitted tree against the original. Any difference is printed in full — it would
mean the two halves of the pipeline have drifted apart.

Run it (from the package dir, or via ``task decompiler:roundtrip``)::

    uv run --package grimmcraft-decompiler python examples/roundtrip_examples.py
"""

# Imports
import sys
from pathlib import Path

from grimmclub import banner
from grimmcraft_decompiler import decompile, roundtrip
from grimmcraft_decompiler.roundtrip import Level

# Constants
EXAMPLES = Path(__file__).resolve().parents[2] / "grimmcraft-compiler" / "examples" / "generated"


# Code
def check(pack: Path) -> bool:
    """Round-trip one pack at the strongest level it supports; return True if identical."""
    result = decompile(pack, emit="machine")
    with result.source:
        level = Level.MACHINE if result.machines else Level.IR
        report = roundtrip(
            result.source,
            result.pack,
            result.target,
            machines=result.machines or None,
            level=level,
        )
        mark = "✓" if report.identical else "✗"
        print(f"  {mark} {pack.name:<24} {report.summary()}")
        if not report.identical:
            for difference in report.differences:
                print(difference.render())
        return report.identical


# Main function
def main() -> None:
    if not EXAMPLES.is_dir():
        print(f"no example packs at {EXAMPLES} — run `task compiler:example` first")
        return

    banner("round-tripping the committed example datapacks")
    packs = sorted(p for p in EXAMPLES.iterdir() if p.is_dir() and any(p.iterdir()))
    results = [check(pack) for pack in packs]

    if all(results):
        print(f"\nAll {len(results)} pack(s) recompiled byte-identically.")
        return
    print(f"\n{results.count(False)} of {len(results)} pack(s) differ.")
    sys.exit(1)


# Call main when script is executed
if __name__ == "__main__":
    main()
