#!/usr/bin/env python
"""Compile the grimmcraft demo machines for two different targets.

Runs the Door + Furnace state machines from ``grimmcraft-control`` through the
compiler for **1.20.4 vanilla** and **1.21.11 vanilla**, and prints the differences
the target makes (folder scheme, ``pack_format``, and NBT-vs-components item data).

Run it (from the package dir, or via ``task compiler:example``)::

    uv run --package grimmcraft-compiler python examples/compile_demos.py
"""

# Imports
from dis import show_code

from grimmcraft_compiler import Target, compile_machines, show_info
from grimmcraft_control.demos import door_machine, furnace_machine

# Constants
TARGETS = [("1.20.4", "vanilla"), ("1.21.11", "vanilla")]

# Main function
def main() -> None:
    for version, flavor in TARGETS:
        target = Target.resolve(version, flavor)
        machines = [door_machine(), furnace_machine()]
        output = f"examples/generated/demo-{version}-{flavor}"
        result = compile_machines(machines, target, namespace="grimmcraft", output=output)

        show_info(target)

        # The one line that differs between the two targets (components vs NBT).
        _id, text = next(
            (fid, t) for fid, t in result.rendered().items()
            if fid.endswith("do_done__collect__empty")
        )
        give_line = next(line for line in text.splitlines() if line.startswith("give"))
        print(f"  give line   : {give_line}")

# Call main when executed
if __name__ == "__main__":
    main()
