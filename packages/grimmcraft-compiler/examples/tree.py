#!/usr/bin/env python
"""Example: compile a machine that grows a parametric oak tree.

A simple procedural tree, using ``fill`` for runs of blocks (not one ``setblock``
per cell):

* **Trunk** — a single vertical ``fill`` of ``TRUNK_HEIGHT`` logs.
* **Canopy** — one ``fill`` per leaf layer (``mode="keep"`` so leaves only land in
  air and never overwrite the trunk), then a few ``setblock``\\ s to round the
  corners.
* **Chop** — one ``fill`` that clears the whole bounding box back to air.

``grow`` places the tree, ``chop`` removes it. Change ``TRUNK_HEIGHT`` /
``LEAF_RADIUS`` to resize it.

Run it::

    uv run --package grimmcraft-compiler python examples/tree.py
"""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path
from typing import Any

from grimmcraft_compiler import Target, compile_machines
from grimmcraft_compiler.dialect import Dialect
from grimmcraft_compiler.emit import render_function
from grimmcraft_control.machine import Machine, fill, new_machine, say, setblock
from grimmcraft_core import BlockPos
from grimmcraft_data import Block

BASE = BlockPos(0, 64, 0)  # the block the trunk grows from
TRUNK_HEIGHT = 5
LEAF_RADIUS = 2
GENERATED = Path(__file__).resolve().parent / "generated"


class Event(StrEnum):
    """The tree's events (named once here, referenced by member below)."""

    GROW = "grow"
    CHOP = "chop"


def build_tree() -> Machine[dict[str, Any]]:
    """A ``tree`` machine: ``grow`` plants it, ``chop`` clears it to air.

    Runs of blocks use ``fill``, not one ``setblock`` each — the trunk is a single
    vertical fill, each leaf layer is one fill, and ``chop`` clears the whole
    bounding box in one command.
    """
    top = TRUNK_HEIGHT - 1
    r_wide = LEAF_RADIUS
    r_narrow = LEAF_RADIUS - 1

    builder = new_machine("tree")

    # Keep each state in a variable and refer to it by that variable below, so a
    # state name is written exactly once (no strings to keep in sync).
    bare = builder.add_state("BARE")

    grown = builder.add_state("GROWN")
    grown.on_enter(say("A tree grows."))

    # Trunk: one vertical fill from the base up.
    grown.on_enter(fill(BASE, BASE.offset(0, top, 0), Block.OAK_LOG))

    # Canopy: two wide leaf slabs around the top, then two narrower ones above.
    # mode="keep" fills only air, so the leaves never overwrite the trunk.
    for y, r in ((top - 1, r_wide), (top, r_wide),
                 (top + 1, r_narrow), (top + 2, r_narrow)):
        grown.on_enter(
            fill(BASE.offset(-r, y, -r), BASE.offset(r, y, r),
                 Block.OAK_LEAVES, mode="keep")
        )

    # Round off the two wide layers by clearing their four corners.
    for y in (top - 1, top):
        for cx in (-r_wide, r_wide):
            for cz in (-r_wide, r_wide):
                grown.on_enter(setblock(BASE.offset(cx, y, cz), Block.AIR))

    builder.transition(bare, Event.GROW, to=grown)

    # Chop: clear the whole tree's bounding box in a single fill.
    chop = builder.add_transition(grown, Event.CHOP, to=bare)
    chop.do(
        fill(BASE.offset(-r_wide, 0, -r_wide),
             BASE.offset(r_wide, top + 2, r_wide), Block.AIR)
    )

    builder.initial(bare)
    return builder.build()


def main() -> None:
    tree = build_tree()
    target = Target.resolve("1.21.1", "vanilla")
    result = compile_machines(
        [tree], target, namespace="grove", output=GENERATED / "tree"
    )

    print(f"target    : {target}")
    print(f"ok        : {result.ok}")
    print(f"functions : {len(result.pack.functions)}")
    print(f"output    : {result.output_path}")

    dialect = Dialect(target)
    grow_fn = next(f for f in result.pack.functions if f.id.path.endswith("grow__grown"))
    print(f"\n# {grow_fn.id}:")
    print(render_function(grow_fn, dialect).rstrip())
    print(f"\nTrigger in-game with: /function grove:{tree.name}/on_{Event.GROW}")


if __name__ == "__main__":
    main()
