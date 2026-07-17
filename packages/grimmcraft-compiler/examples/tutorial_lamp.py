#!/usr/bin/env python
"""Tutorial: build a machine from scratch and compile it to a datapack.

This is the "learn the API in one file" example. It builds a **redstone lamp**
state machine by hand (no demo helpers), compiles it for one target, and prints
the generated ``mcfunction`` so you can see exactly how each primitive lowers.

The API is built for readability: states and transitions are added one method
call at a time (``builder.add_state(...)`` → ``on_enter(...)`` / ``on_cycle(...)``),
and commands come from typed constructors (``setblock``, ``say``, ``playsound``,
``set_score``, ``add_score``) instead of raw ``Command(name, payload-dict)``. The
lamp's states and events are the ``LampState`` / ``LampEvent`` enums below.

The lamp:

* ``OFF`` / ``ON`` states, toggled by a ``pull`` event (a lever, a button, …).
* Turning ``ON`` lights the block, plays a click, and arms a 100-tick timer.
* While ``ON``, a per-tick **cycle** counts the timer down; an automatic
  ``TICK`` transition switches it back ``OFF`` when the timer hits zero — so the
  lamp auto-offs without anyone sending an event.

Run it::

    uv run --package grimmcraft-compiler python examples/tutorial_lamp.py
"""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path
from typing import Any

# grimmcraft-compiler is the backend: it turns a machine into a datapack.
from grimmcraft_compiler import Target, compile_machines
from grimmcraft_compiler.dialect import Dialect
from grimmcraft_compiler.emit import render_function

# grimmcraft-control is where behaviour lives: the machine + its primitives, plus
# the CommandName / ConditionName vocabularies so nothing is stringly-typed.
from grimmcraft_control.machine import (
    TICK_EVENT,
    Machine,
    MachineBuilder,
    add_score,
    playsound,
    say,
    set_score,
    setblock,
)

# grimmcraft-core gives us real world types to reuse (here: a block position).
from grimmcraft_core import BlockPos

# grimmcraft-data is the id source of truth; using an enum member means the id is
# valid by construction (the compiler won't need to guess or warn).
from grimmcraft_data import Block

LAMP_POS = BlockPos(0, 64, 0)
TIMER = "lamp_timer"

# Write the datapack next to this example (a tracked, committed reference copy)
# rather than into the gitignored dist/, so the generated output is visible in
# the repo. Re-running this script refreshes it in place.
GENERATED = Path(__file__).resolve().parent / "generated"


class LampState(StrEnum):
    """This machine's states (a StrEnum, so each member is its own name)."""

    OFF = "OFF"
    ON = "ON"


class LampEvent(StrEnum):
    """This machine's events."""

    PULL = "pull"


def build_lamp() -> Machine[dict[str, Any]]:
    """Assemble the lamp machine one step at a time.

    We keep a ``builder`` variable and add each state/transition with its own
    method call. Commands come from the typed constructors (``setblock``,
    ``say``, …) so there are no payload dicts or ``Command(...)`` wrappers — every
    line reads like a sentence and can be commented out or reordered on its own.
    """
    # The context (here an empty dict) is whatever runtime state your handlers
    # need; the compiler doesn't use it, so keep it simple.
    builder = MachineBuilder[dict[str, Any]]({})
    builder.named("lamp")  # the grimmcraft_state scoreboard entry + function folder
    builder.for_entity(Block.REDSTONE_LAMP.string_id)  # type: ignore[attr-defined]

    # 1. The OFF state: remove the light so the area goes dark. `on_enter` runs
    #    once, when the machine enters the state; "off" is just setting air.
    off = builder.add_state(LampState.OFF)
    off.on_enter(setblock(LAMP_POS, Block.AIR))

    # 2. The ON state: place a full-bright invisible light, click, announce it,
    #    and arm a 100-tick timer — one command per line. `minecraft:light[level=15]`
    #    emits light 15 with no visible block and stays lit with no redstone.
    #    `on_cycle` runs every tick while the machine sits in this state.
    on = builder.add_state(LampState.ON)
    on.on_enter(setblock(LAMP_POS, Block.LIGHT, level=15))
    on.on_enter(playsound("minecraft:block.lever.click"))
    on.on_enter(say("The lamp glows."))
    on.on_enter(set_score(TIMER, "lamp", 100))
    on.on_cycle(add_score(TIMER, "lamp", -1))

    # 3. Pulling the lever toggles between OFF and ON (event transitions).
    builder.transition(LampState.OFF, LampEvent.PULL, to=LampState.ON)
    builder.transition(LampState.ON, LampEvent.PULL, to=LampState.OFF)

    # 4. An automatic transition: checked every tick, *after* ON's cycle commands.
    #    `when_score` turns the lamp off once the timer reaches 0; it becomes an
    #    `execute if score …` guard in the datapack.
    auto = builder.add_transition(LampState.ON, TICK_EVENT, to=LampState.OFF)
    auto.when_score(TIMER, "lamp", 0)

    # 5. Start in OFF, then freeze the definition into an immutable Machine.
    builder.initial(LampState.OFF)
    return builder.build()


def main() -> None:
    lamp = build_lamp()
    target = Target.resolve("1.21.1", "vanilla")

    # Compile: collect → IR → validate → render → emit → verify, all in one call.
    result = compile_machines(
        [lamp], target, namespace="tutorial", output=GENERATED / "tutorial-lamp"
    )

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
