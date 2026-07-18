#!/usr/bin/env python
"""Example: compile a machine that grows a parametric spruce (conifer).

A stack of shrinking square leaf rings around a tall trunk — wide at the base,
tapering to a single-block tip. That cone shape is exactly what layered ``fill``\\ s
produce, so a conifer is the natural fit (a rounded oak would need carved corners).

* **Trunk** — one vertical ``fill`` of ``TRUNK_HEIGHT`` spruce logs.
* **Foliage** — one ``fill`` per ring in :data:`FOLIAGE` (``mode="keep"`` so leaves
  only land in air and never overwrite the trunk).
* **Chop** — one ``fill`` that clears the whole bounding box back to air.

``grow`` places the spruce, ``chop`` removes it. Edit ``TRUNK_HEIGHT`` / ``FOLIAGE``
to reshape it.

Run it (from the package dir, or via ``task compiler:tree``)::

    uv run --package grimmcraft-compiler python examples/tree.py
"""

from grimmclub import StrEnum
from grimmcraft_compiler import Target, compile_machines
from grimmcraft_control import MachineDefault, new_machine
from grimmcraft_core import BlockPos, BlockType

BASE = BlockPos(0, 64, 0)  # the block the trunk grows from
TRUNK_HEIGHT = 6
# Foliage rings, bottom to top, as (y offset, radius): widest at the base,
# shrinking to a single-block tip — the classic conifer silhouette.
FOLIAGE = ((2, 2), (3, 2), (4, 1), (5, 1), (6, 1), (7, 0))
OUTPUT = "examples/generated/spruce"


class Event(StrEnum):
    """The spruce's events (named once here, referenced by member below)."""

    GROW = "grow"
    CHOP = "chop"


def build_spruce() -> MachineDefault:
    """A ``spruce`` machine: ``grow`` plants it, ``chop`` clears it to air."""
    builder = new_machine("spruce")

    # Keep each state in a variable and refer to it by that variable below, so a
    # state name is written exactly once (no strings to keep in sync).
    bare = builder.add_state("BARE")

    grown = builder.add_state("GROWN")
    grown.enter.say("A spruce grows.")

    # Trunk: one vertical fill from the base up.
    grown.enter.fill(BASE, BASE.offset(0, TRUNK_HEIGHT - 1, 0), BlockType.SPRUCE_LOG)

    # Foliage: one fill per ring, widest at the bottom and tapering to the tip.
    # mode="keep" fills only air, so the leaves never overwrite the trunk.
    for y, r in FOLIAGE:
        grown.enter.fill(
            BASE.offset(-r, y, -r), BASE.offset(r, y, r),
            BlockType.SPRUCE_LEAVES, mode="keep",
        )

    builder.transition(bare, Event.GROW, to=grown)

    # Chop: clear the whole bounding box in a single fill.
    max_r = max(r for _y, r in FOLIAGE)
    top_y = FOLIAGE[-1][0]
    chop = builder.add_transition(grown, Event.CHOP, to=bare)
    chop.do.fill(
        BASE.offset(-max_r, 0, -max_r), BASE.offset(max_r, top_y, max_r), BlockType.AIR
    )

    builder.initial(bare)
    return builder.build()


def main() -> None:
    spruce = build_spruce()
    target = Target.resolve("1.21.1", "vanilla")
    result = compile_machines([spruce], target, namespace="grove", output=OUTPUT)

    print(f"target    : {target}")
    print(f"ok        : {result.ok}")
    print(f"functions : {len(result.pack.functions)}")
    print(f"output    : {result.output_path}")

    grow_id, grow_text = next(
        (fid, text) for fid, text in result.rendered().items()
        if fid.endswith("grow__grown")
    )
    print(f"\n# {grow_id}:")
    print(grow_text.rstrip())
    print(f"\nTrigger in-game with: /function grove:{spruce.name}/on_{Event.GROW}")


if __name__ == "__main__":
    main()
