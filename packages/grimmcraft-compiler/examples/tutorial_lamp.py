#!/usr/bin/env python
"""Tutorial: build a machine from scratch and compile it to a datapack.

This is the "learn the API in one file" example. It builds a **redstone lamp**
state machine by hand, compiles it, and prints the generated ``mcfunction`` so you
can see how each primitive lowers.

The API avoids ceremony and magic strings:

* ``new_machine("lamp")`` starts a builder — no generics, no context object.
* ``builder.add_state("OFF")`` returns a state; refer to it by that variable in
  transitions, so a state name is written exactly once.
* effects are **methods on the state** — ``on.enter.setblock(...)`` /
  ``on.cycle.add_score(...)`` — so there are no effect imports.
* the one repeated event name lives in the small ``Event`` enum.

Run it (from the package dir, or via ``task compiler:tutorial``)::

    uv run --package grimmcraft-compiler python examples/tutorial_lamp.py
"""

# Imports
from grimmclub import StrEnum, banner, no
from grimmcraft_compiler import Target, compile_machines
from grimmcraft_control import TICK_EVENT, MachineDefault, new_machine
from grimmcraft_core import BlockPos, BlockType

# Constants
LAMP_POS = BlockPos(0, 64, 0)
TIMER = "lamp_timer"
# Committed reference copy lives next to the examples (run via `task`, whose cwd
# is the package dir). See examples/generated/README.md.
OUTPUT = "examples/generated/tutorial-lamp"

# Types
class Event(StrEnum):
    """This machine's events. Using an enum means the repeated ``pull`` below is
    written once and can't be mistyped (states are referenced by variable, so
    they don't need an enum)."""

    PULL = "pull"

# Code
def build_lamp() -> MachineDefault:
    """Assemble the lamp machine one step at a time."""
    builder = new_machine("lamp")
    builder.for_entity(BlockType.REDSTONE_LAMP.string_id)  # type: ignore[attr-defined]

    # 1. OFF: remove the light so the area goes dark. A `with` block groups the
    #    state's definition; `off` stays usable afterwards (in the transitions).
    #    `enter` effects run once, when the machine enters the state.
    with builder.add_state("OFF") as off:
        off.enter.setblock(LAMP_POS, BlockType.AIR)

    # 2. ON: place a full-bright invisible light, click, announce it, and arm a
    #    100-tick timer — one method call per effect. light[level=15] emits light
    #    15 with no visible block and stays lit with no redstone. `cycle` effects
    #    run every tick while in the state.
    with builder.add_state("ON") as on:
        on.enter.setblock(LAMP_POS, BlockType.LIGHT, level=15)
        on.enter.playsound("minecraft:block.lever.click")
        on.enter.say("The lamp glows.")
        on.enter.set_score(TIMER, "lamp", 100)
        on.cycle.add_score(TIMER, "lamp", -1)

    # 3. Pulling the lever toggles the two states — pass the state objects.
    builder.transition(off, Event.PULL, to=on)
    builder.transition(on, Event.PULL, to=off)

    # 4. Automatic: checked every tick, *after* ON's cycle. Turn the lamp off once
    #    the timer reaches 0 (becomes an `execute if score …` guard).
    auto = builder.add_transition(on, TICK_EVENT, to=off)
    auto.when_score(TIMER, "lamp", 0)

    # 5. Start in OFF, then freeze the definition into an immutable Machine.
    builder.initial(off)
    return builder.build()

# Main function
def main() -> None:
    lamp = build_lamp()
    target = Target.resolve("1.21.11", "vanilla")

    # Compile: collect → IR → validate → render → emit → verify, all in one call.
    result = compile_machines([lamp], target, namespace="tutorial", output=OUTPUT, DEBUG=no)

    # Show input → output: every generated function's rendered mcfunction text.
    banner("generated mcfunction")  # a grimmclub teaching helper
    for function_id, text in result.rendered().items():
        print(f"# ---- {function_id} ----")
        print(text.rstrip())
        print()

# Call main when script is executed
if __name__ == "__main__":
    main()
