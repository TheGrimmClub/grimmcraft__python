#!/usr/bin/env python
"""Compile the grimmcraft demo machines for two different targets.

Runs the Door + Furnace state machines from ``grimmcraft-control`` through the
compiler for **1.20.4 vanilla** and **1.21.1 vanilla**, and prints the differences
the target makes (folder scheme, ``pack_format``, and NBT-vs-components item data).

Run it (from the package dir, or via ``task compiler:example``)::

    uv run --package grimmcraft-compiler python examples/compile_demos.py
"""

from grimmcraft_compiler import Target, compile_machines
from grimmcraft_control.demos import door_machine, furnace_machine

TARGETS = [("1.20.4", "vanilla"), ("1.21.1", "vanilla")]


def main() -> None:
    for version, flavor in TARGETS:
        target = Target.resolve(version, flavor)
        machines = [door_machine(), furnace_machine()]
        output = f"examples/generated/demo-{version}-{flavor}"
        result = compile_machines(machines, target, namespace="grimmcraft", output=output)

        info = target.info
        folder = "function" if info.singular_folders else "functions"
        data_model = "components" if info.uses_components else "NBT tags"
        print(f"\n=== {target} ===")
        print(f"  pack_format : {info.pack_format}")
        print(f"  folders     : data/<ns>/{folder}/…")
        print(f"  item data   : {data_model}")
        print(f"  functions   : {len(result.pack.functions)}")
        print(f"  output      : {result.output_path}")

        # The one line that differs between the two targets (components vs NBT).
        _id, text = next(
            (fid, t) for fid, t in result.rendered().items()
            if fid.endswith("do_done__collect__empty")
        )
        give_line = next(line for line in text.splitlines() if line.startswith("give"))
        print(f"  give line   : {give_line}")


if __name__ == "__main__":
    main()
