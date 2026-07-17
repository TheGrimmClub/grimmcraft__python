#!/usr/bin/env python
"""Tutorial: build a machine from scratch and compile it to a datapack.

This is the "learn the API in one file" example. It builds a **redstone lamp**
state machine by hand (no demo helpers), compiles it for one target, and prints
the generated ``mcfunction`` so you can see exactly how each primitive lowers.

Identifiers are **enums, not magic strings**: command kinds come from
``CommandName`` / ``ConditionName`` (both ``StrEnum``, so they *are* their string
value), and the lamp's own states and events are the ``LampState`` / ``LampEvent``
enums declared below. The compiler validates ids the same way either style is
used — enums just make typos impossible and let editors autocomplete.

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
    Command,
    CommandName,
    Condition,
    ConditionName,
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


class LampState(StrEnum):
    """This machine's states (a StrEnum, so each member is its own name)."""

    OFF = "OFF"
    ON = "ON"


class LampEvent(StrEnum):
    """This machine's events."""

    PULL = "pull"


def build_lamp() -> Machine[dict[str, Any]]:
    """Assemble the lamp machine one step at a time.

    We keep a ``builder`` variable and call one method per line instead of
    chaining them together. Each line does exactly one thing, so you can read it
    top-to-bottom, comment a line out, or reorder steps without untangling a
    single big expression.
    """
    # The context (here an empty dict) is whatever runtime state your handlers
    # need; the compiler doesn't use it, so keep it simple.
    builder = MachineBuilder[dict[str, Any]]({})
    builder.named("lamp")  # the grimmcraft_state scoreboard entry + function folder
    builder.for_entity(Block.REDSTONE_LAMP.string_id)  # type: ignore[attr-defined]

    # 1. The OFF state: remove the light so the area goes dark when we land here.
    #    `enter` commands run once, when the machine enters the state. We use the
    #    invisible `minecraft:light` block, so "off" just means setting it to air.
    builder.state(
        LampState.OFF,
        enter=(
            Command(CommandName.SETBLOCK, {"pos": LAMP_POS, "block": Block.AIR}),
        ),
    )

    # 2. The ON state: place a full-bright invisible light, click, announce it,
    #    and arm a 100-tick timer. `minecraft:light[level=15]` emits light 15 with
    #    no visible block and — unlike a redstone_lamp — stays lit with no power.
    #    `cycle` commands run every tick while the machine sits in this state.
    builder.state(
        LampState.ON,
        enter=(
            Command(
                CommandName.SETBLOCK,
                {"pos": LAMP_POS, "block": Block.LIGHT, "state": {"level": "15"}},
            ),
            Command(CommandName.PLAYSOUND, {"sound": "minecraft:block.lever.click"}),
            Command(CommandName.SAY, {"text": "The lamp glows."}),
            Command(
                CommandName.SCOREBOARD_SET,
                {"objective": TIMER, "entry": "lamp", "value": 100},
            ),
        ),
        cycle=(
            Command(
                CommandName.SCOREBOARD_ADD,
                {"objective": TIMER, "entry": "lamp", "value": -1},
            ),
        ),
    )

    # 3. Pulling the lever toggles between OFF and ON (an event transition).
    builder.transition(LampState.OFF, LampEvent.PULL, to=LampState.ON)
    builder.transition(LampState.ON, LampEvent.PULL, to=LampState.OFF)

    # 4. An automatic transition: TICK_EVENT is checked every tick, *after* ON's
    #    cycle commands. When the timer hits 0 the lamp turns itself off. The
    #    Condition becomes an `execute if score …` guard in the datapack.
    builder.transition(
        LampState.ON,
        TICK_EVENT,
        to=LampState.OFF,
        condition=Condition(
            ConditionName.SCORE_MATCHES,
            {"objective": TIMER, "entry": "lamp", "value": 0},
        ),
    )

    # 5. Start in OFF, then freeze the definition into an immutable Machine.
    builder.initial(LampState.OFF)
    return builder.build()


def main() -> None:
    lamp = build_lamp()
    target = Target.resolve("1.21.1", "vanilla")

    # Compile: collect → IR → validate → render → emit → verify, all in one call.
    result = compile_machines(
        [lamp], target, namespace="tutorial", output=Path("dist/tutorial-lamp")
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
