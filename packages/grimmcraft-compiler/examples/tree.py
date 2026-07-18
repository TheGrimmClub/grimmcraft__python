#!/usr/bin/env python
"""Example: compile a machine that grows a parametric oak tree.

A simple procedural tree algorithm, computed in Python and baked into the
datapack:

* **Trunk** — stack ``TRUNK_HEIGHT`` logs straight up from the base.
* **Canopy** — leaves in a few square layers around the top, with the corners
  trimmed so the blob looks round, and never overwriting the trunk.

``grow`` places the tree, ``chop`` clears everything it occupies back to air.
Change ``TRUNK_HEIGHT`` / ``LEAF_RADIUS`` to resize it.

Run it::

    uv run --package grimmcraft-compiler python examples/tree.py
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from grimmcraft_compiler import Target, compile_machines
from grimmcraft_compiler.dialect import Dialect
from grimmcraft_compiler.emit import render_function
from grimmcraft_control.machine import Machine, MachineBuilder, say, setblock
from grimmcraft_core import BlockPos
from grimmcraft_data import Block

BASE = BlockPos(0, 64, 0)  # the block the trunk grows from
TRUNK_HEIGHT = 5
LEAF_RADIUS = 2
GENERATED = Path(__file__).resolve().parent / "generated"


def _tree_blocks() -> list[tuple[BlockPos, Any]]:
    """Compute every (position, block) the tree occupies — trunk then canopy.

    Returned in a stable order so the generated datapack is deterministic.
    """
    blocks: list[tuple[BlockPos, Any]] = []

    # Trunk: a column of logs.
    trunk = [(0, y, 0) for y in range(TRUNK_HEIGHT)]
    trunk_cells = set(trunk)
    for dx, dy, dz in trunk:
        blocks.append((BASE.offset(dx, dy, dz), Block.OAK_LOG))

    # Canopy: two wide leaf layers around the top, then two narrower ones above.
    top = TRUNK_HEIGHT - 1
    layers = [
        (top - 1, LEAF_RADIUS),
        (top, LEAF_RADIUS),
        (top + 1, LEAF_RADIUS - 1),
        (top + 2, LEAF_RADIUS - 1),
    ]
    for y, r in layers:
        for dx in range(-r, r + 1):
            for dz in range(-r, r + 1):
                if abs(dx) == r and abs(dz) == r:
                    continue  # trim the corners so the canopy is round
                if (dx, y, dz) in trunk_cells:
                    continue  # don't overwrite the trunk
                blocks.append((BASE.offset(dx, y, dz), Block.OAK_LEAVES))
    return blocks


def build_tree() -> Machine[dict[str, Any]]:
    """A ``tree`` machine: ``grow`` plants it, ``chop`` clears it to air."""
    blocks = _tree_blocks()

    builder = MachineBuilder[dict[str, Any]]({})
    builder.named("tree")
    builder.add_state("BARE")

    grown = builder.add_state("GROWN")
    grown.on_enter(say("A tree grows."))
    for pos, block in blocks:
        grown.on_enter(setblock(pos, block))

    builder.transition("BARE", "grow", to="GROWN")
    chop = builder.add_transition("GROWN", "chop", to="BARE")
    for pos, _block in blocks:
        chop.do(setblock(pos, Block.AIR))

    builder.initial("BARE")
    return builder.build()


def main() -> None:
    tree = build_tree()
    target = Target.resolve("1.21.1", "vanilla")
    result = compile_machines(
        [tree], target, namespace="grove", output=GENERATED / "tree"
    )

    logs = sum(1 for pos, b in _tree_blocks() if b is Block.OAK_LOG)
    leaves = sum(1 for pos, b in _tree_blocks() if b is Block.OAK_LEAVES)
    print(f"target    : {target}")
    print(f"ok        : {result.ok}")
    print(f"functions : {len(result.pack.functions)}")
    print(f"blocks    : {logs} logs + {leaves} leaves")
    print(f"output    : {result.output_path}")

    dialect = Dialect(target)
    grow_fn = next(f for f in result.pack.functions if f.id.path.endswith("grow__grown"))
    lines = render_function(grow_fn, dialect).splitlines()
    print(f"\n# {grow_fn.id}  ({len(lines)} lines) — first 8:")
    print("\n".join(lines[:8]))
    print(f"Trigger in-game with: /function grove:{tree.name}/on_grow")


if __name__ == "__main__":
    main()
