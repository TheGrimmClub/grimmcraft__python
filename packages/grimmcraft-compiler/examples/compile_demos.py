#!/usr/bin/env python
"""Compile the grimmcraft demo machines for two different targets.

Runs the Door + Furnace state machines from ``grimmcraft-control`` through the
compiler for **1.20.4 vanilla** and **1.21.1 vanilla**, writing two datapacks
into ``dist/examples/`` and printing the differences the target makes (folder
scheme, ``pack_format``, and NBT-vs-components item data).

Run it with::

    uv run --package grimmcraft-compiler python examples/compile_demos.py
"""

from __future__ import annotations

from pathlib import Path

from grimmcraft_compiler import Target, compile_machines
from grimmcraft_control.demos import door_machine, furnace_machine

# Write next to this example (tracked, committed reference copies) instead of the
# gitignored dist/, so the generated datapacks are visible in the repo.
OUT = Path(__file__).resolve().parent / "generated"
TARGETS = [("1.20.4", "vanilla"), ("1.21.1", "vanilla")]


def main() -> None:
    for version, flavor in TARGETS:
        target = Target.resolve(version, flavor)
        machines = [door_machine(), furnace_machine()]
        out_dir = OUT / f"demo-{version}-{flavor}"
        result = compile_machines(machines, target, namespace="grimmcraft",
                                  output=out_dir)

        info = target.info
        folder = "function" if info.singular_folders else "functions"
        data_model = "components" if info.uses_components else "NBT tags"
        print(f"\n=== {target} ===")
        print(f"  pack_format : {info.pack_format}")
        print(f"  folders     : data/<ns>/{folder}/…")
        print(f"  item data   : {data_model}")
        print(f"  functions   : {len(result.pack.functions)}")
        print(f"  diagnostics : {len(result.diagnostics.errors)} error(s), "
              f"{len(result.diagnostics.warnings)} warning(s)")
        print(f"  output      : {result.output_path}")

        # Show the one line that differs between the two targets.
        give = (out_dir / "data/grimmcraft" / folder
                / "furnace/do_done__collect__empty.mcfunction")
        for line in give.read_text().splitlines():
            if line.startswith("give"):
                print(f"  give line   : {line}")


if __name__ == "__main__":
    main()
