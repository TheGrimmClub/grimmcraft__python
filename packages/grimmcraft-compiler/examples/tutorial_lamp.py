#!/usr/bin/env python
"""Tutorial: build a machine from scratch and compile it to a datapack.

This is the "learn the API in one file" example. It builds a **redstone lamp**
state machine by hand (no demo helpers), compiles it for one target, and prints
the generated ``mcfunction`` so you can see exactly how each primitive lowers.

The lamp:

* ``OFF`` / ``ON`` states, toggled by a ``pull`` event (a lever, a button, …).
* Turning ``ON`` lights the block, plays a click, and arms a 100-tick timer.
* While ``ON``, a per-tick **cycle** counts the timer down; an automatic
  ``"tick"`` transition switches it back ``OFF`` when the timer hits zero — so
  the lamp auto-offs without anyone sending an event.

Run it::

    uv run --package grimmcraft-compiler python examples/tutorial_lamp.py
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

# grimmcraft-compiler is the backend: it turns a machine into a datapack.
from grimmcraft_compiler import Target, compile_machines
from grimmcraft_compiler.dialect import Dialect
from grimmcraft_compiler.emit import render_function

# grimmcraft-control is where behaviour lives: the state machine + its primitives.
from grimmcraft_control.machine import (
    TICK_EVENT,
    Command,
    Condition,
    Machine,
    MachineBuilder,
)

# grimmcraft-core gives us real world types to reuse (here: a block position).
from grimmcraft_core import BlockPos

# grimmcraft-data is the id source of truth; using an enum member means the id is
# valid by construction (the compiler won't need to guess or warn).
from grimmcraft_data import Block

LAMP_POS = BlockPos(0, 64, 0)
TIMER = "lamp_timer"


def build_lamp() -> Machine[dict[str, Any]]:
    """Assemble the lamp machine with the fluent builder DSL."""
    return (
        # The context (here an empty dict) is whatever runtime state your handlers
        # need; the compiler doesn't use it, so keep it simple.
        MachineBuilder[dict[str, Any]]({})
        .named("lamp")  # names the grimmcraft_state scoreboard entry + function folder
        .for_entity(Block.REDSTONE_LAMP.string_id)  # optional: bind to a block id
        # --- states -------------------------------------------------------
        .state(
            "OFF",
            # enter commands run once when the machine lands in this state.
            enter=(
                Command("setblock", {"pos": LAMP_POS, "block": Block.REDSTONE_LAMP,
                                     "state": {"lit": "false"}}),
            ),
        )
        .state(
            "ON",
            enter=(
                Command("setblock", {"pos": LAMP_POS, "block": Block.REDSTONE_LAMP,
                                     "state": {"lit": "true"}}),
                Command("playsound", {"sound": "minecraft:block.lever.click"}),
                Command("say", {"text": "The lamp glows."}),
                # arm the auto-off timer
                Command("scoreboard_set", {"objective": TIMER, "entry": "lamp",
                                           "value": 100}),
            ),
            # cycle commands run every tick while in this state (the processing
            # loop). Here: burn the timer down by one each tick.
            cycle=(
                Command("scoreboard_add", {"objective": TIMER, "entry": "lamp",
                                           "value": -1}),
            ),
        )
        # --- transitions --------------------------------------------------
        # An event transition: fires when you dispatch/emit the "pull" event.
        .transition("OFF", "pull", to="ON")
        .transition("ON", "pull", to="OFF")
        # An automatic transition: event TICK_EVENT means "check every tick,
        # after the cycle commands". The declarative Condition is what the
        # compiler lowers into an `execute if score …` guard.
        .transition(
            "ON", TICK_EVENT, to="OFF",
            condition=Condition("score_matches", {"objective": TIMER,
                                                  "entry": "lamp", "value": 0}),
        )
        .initial("OFF")
        .build()
    )


def main() -> None:
    lamp = build_lamp()
    target = Target.resolve("1.21.1", "vanilla")

    # Compile: collect → IR → validate → render → emit → verify, all in one call.
    result = compile_machines([lamp], target, namespace="tutorial",
                              output=Path("dist/tutorial-lamp"))

    print(f"target      : {target}")
    print(f"ok          : {result.ok}")
    print(f"functions   : {len(result.pack.functions)}")
    print(f"output      : {result.output_path}\n")

    # Show input → output: render every generated function with the dialect so
    # you can see how states/transitions/cycle became mcfunction lines.
    dialect = Dialect(target)
    for function in result.pack.functions:
        print(f"# ---- {function.id} ----")
        print(render_function(function, dialect).rstrip())
        print()


if __name__ == "__main__":
    main()
