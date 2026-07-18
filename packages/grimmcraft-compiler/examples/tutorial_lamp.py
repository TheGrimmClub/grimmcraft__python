#!/usr/bin/env python
"""Tutorial: build a machine from scratch and compile it to a datapack.

This is the "learn the API in one file" example. It builds a **redstone lamp**
state machine by hand (no demo helpers), compiles it for one target, and prints
the generated ``mcfunction`` so you can see exactly how each primitive lowers.

The API is built for readability, avoiding magic strings you have to keep in sync:

* ``new_machine("lamp")`` starts a builder — no generics or context to pass.
* ``builder.add_state("OFF")`` returns a state object; refer to it by that
  variable in transitions, so each state name is written exactly once.
* commands come from typed constructors (``setblock``, ``say``, ``playsound``,
  ``set_score``, ``add_score``) — no ``Command(name, payload-dict)``.
* the one repeated event name lives in the small ``Event`` enum below.

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
    add_score,
    new_machine,
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


class Event(StrEnum):
    """This machine's events. Using an enum means the repeated ``pull`` below is
    written once and can't be mistyped (states are referenced by variable, so
    they don't need an enum)."""

    PULL = "pull"


def build_lamp() -> Machine[dict[str, Any]]:
    """Assemble the lamp machine one step at a time.

    We keep a ``builder`` variable and add each state/transition with its own
    method call. Commands come from the typed constructors (``setblock``,
    ``say``, …) so there are no payload dicts or ``Command(...)`` wrappers — every
    line reads like a sentence and can be commented out or reordered on its own.
    """
    # Start a machine called "lamp" (this name is its grimmcraft_state scoreboard
    # entry and its function folder). new_machine() hides the generic/context
    # boilerplate — you only need it if you drive the machine at runtime.
    builder = new_machine("lamp")
    builder.for_entity(Block.REDSTONE_LAMP.string_id)  # type: ignore[attr-defined]

    # 1. The OFF state: remove the light so the area goes dark. `on_enter` runs
    #    once, when the machine enters the state; "off" is just setting air. We
    #    keep the returned `off` object and refer to it by variable below, so the
    #    name "OFF" is written exactly once.
    off = builder.add_state("OFF")
    off.on_enter(setblock(LAMP_POS, Block.AIR))

    # 2. The ON state: place a full-bright invisible light, click, announce it,
    #    and arm a 100-tick timer — one command per line. `minecraft:light[level=15]`
    #    emits light 15 with no visible block and stays lit with no redstone.
    #    `on_cycle` runs every tick while the machine sits in this state.
    on = builder.add_state("ON")
    on.on_enter(setblock(LAMP_POS, Block.LIGHT, level=15))
    on.on_enter(playsound("minecraft:block.lever.click"))
    on.on_enter(say("The lamp glows."))
    on.on_enter(set_score(TIMER, "lamp", 100))
    on.on_cycle(add_score(TIMER, "lamp", -1))

    # 3. Pulling the lever toggles between the two states — pass the state objects
    #    (no repeated strings to keep in sync).
    builder.transition(off, Event.PULL, to=on)
    builder.transition(on, Event.PULL, to=off)

    # 4. An automatic transition: checked every tick, *after* ON's cycle commands.
    #    `when_score` turns the lamp off once the timer reaches 0; it becomes an
    #    `execute if score …` guard in the datapack.
    auto = builder.add_transition(on, TICK_EVENT, to=off)
    auto.when_score(TIMER, "lamp", 0)

    # 5. Start in OFF, then freeze the definition into an immutable Machine.
    builder.initial(off)
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
