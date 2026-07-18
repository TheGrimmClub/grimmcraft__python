#!/usr/bin/env python
"""Example: a spruce that *grows over time*, one ring per tick.

Where ``tree.py`` places the whole conifer in a single event, this one uses the
state machine's per-tick **cycle** plus a ``stage`` scoreboard to build it up
gradually — the timer/scoreboard approach:

* ``plant`` resets ``stage`` to 0 and enters ``GROWING``.
* every tick, ``GROWING`` bumps ``stage`` by one, then ``cycle.if_score(...)``
  places just the step matching the new ``stage`` (trunk first, then each ring).
* an automatic transition finishes to ``GROWN`` once the last step is placed.

So the machine iterates over ticks instead of unrolling the whole build into one
function. (One step per tick is quick; real "slow growth" would count a longer
timer down between steps.)

Run it (from the package dir, or via ``task compiler:grow``)::

    uv run --package grimmcraft-compiler python examples/tree_growing.py
"""

# Imports
from grimmclub import StrEnum
from grimmcraft_compiler import Target, compile_machines
from grimmcraft_control import TICK_EVENT, MachineDefault, new_machine
from grimmcraft_core import BlockPos, BlockType

# Constants
BASE = BlockPos(0, 64, 0)
TRUNK_HEIGHT = 6
FOLIAGE = ((2, 2), (3, 2), (4, 1), (5, 1), (6, 1), (7, 0))
STAGE = "spruce_stage"  # scoreboard objective tracking how far grown
ENTRY = "spruce"  # the score holder
OUTPUT = "examples/generated/growing-spruce"

# Types
class Event(StrEnum):
    PLANT = "plant"

# Code
def build_growing_spruce() -> MachineDefault:
    """A spruce that builds itself one step per tick while in ``GROWING``."""
    builder = new_machine("growing_spruce")

    seed = builder.add_state("SEED")
    growing = builder.add_state("GROWING")
    grown = builder.add_state("GROWN")
    grown.enter.say("The spruce is fully grown.")

    # The processing loop: each tick advance the stage, then place only the step
    # whose number now matches — cycle.if_score(...) gates each fill on the score.
    growing.cycle.add_score(STAGE, ENTRY, 1)
    stage = 1
    growing.cycle.if_score(STAGE, ENTRY, stage).fill(
        BASE, BASE.offset(0, TRUNK_HEIGHT - 1, 0), BlockType.SPRUCE_LOG
    )
    for y, r in FOLIAGE:
        stage += 1
        growing.cycle.if_score(STAGE, ENTRY, stage).fill(
            BASE.offset(-r, y, -r), BASE.offset(r, y, r),
            BlockType.SPRUCE_LEAVES, mode="keep",
        )

    # plant (re)starts growth from stage 0.
    builder.add_transition(seed, Event.PLANT, to=growing).do.set_score(STAGE, ENTRY, 0)
    # Automatic: once the last step's stage is reached, finish growing.
    builder.add_transition(growing, TICK_EVENT, to=grown).when_score(STAGE, ENTRY, stage)

    builder.initial(seed)
    return builder.build()

# Main function
def main() -> None:
    spruce = build_growing_spruce()
    target = Target.resolve("1.21.11", "vanilla")
    result = compile_machines([spruce], target, namespace="grove", output=OUTPUT)

    print(f"target    : {target}")
    print(f"ok        : {result.ok}")
    print(f"functions : {len(result.pack.functions)}")
    print(f"output    : {result.output_path}")

    tick_id, tick_text = next(
        (fid, text) for fid, text in result.rendered().items()
        if fid.endswith("tick_growing")
    )
    print(f"\n# {tick_id} (the per-tick growth loop):")
    print(tick_text.rstrip())
    print(f"\nTrigger in-game with: /function grove:{spruce.name}/on_{Event.PLANT}")

# Call main when script is executed
if __name__ == "__main__":
    main()
