"""Ready-made example machines used by the docs, tests and the compiler.

These are ordinary :class:`~grimmcraft_control.machine.Machine` instances built
with the public builder — nothing special.  They exist so the compiler and the
examples share one canonical Door / Furnace definition instead of each inventing
their own.  Commands reference real ``grimmcraft_data`` ids and ``grimmcraft_core``
positions so the compiler's validation has something concrete to check.
"""

from __future__ import annotations

from typing import Any

from grimmcraft_control.machine import (
    TICK_EVENT,
    Command,
    Condition,
    Machine,
    MachineBuilder,
)
from grimmcraft_core import BlockPos
from grimmcraft_data import Block, Item

# A door and a furnace anchored at fixed block positions in the example world.
DOOR_POS = BlockPos(0, 64, 0)
LAMP_POS = BlockPos(0, 65, 0)
FURNACE_POS = BlockPos(3, 64, 0)


def door_machine() -> Machine[dict[str, Any]]:
    """A door with ``CLOSED`` / ``OPEN`` / ``LOCKED`` states.

    ``open`` swaps in a lit redstone lamp and plays the door sound; ``close``
    reverses it; ``lock``/``unlock`` gate the door from ``CLOSED``.
    """
    return (
        MachineBuilder[dict[str, Any]]({})
        .named("door")
        .for_entity(Block.OAK_DOOR.string_id)  # type: ignore[attr-defined]
        .state("CLOSED")
        .state(
            "OPEN",
            enter=(
                Command("setblock", {"pos": LAMP_POS, "block": Block.REDSTONE_LAMP,
                                     "state": {"lit": "true"}}),
                Command("playsound", {"sound": "minecraft:block.wooden_door.open"}),
            ),
            exit=(
                Command("setblock", {"pos": LAMP_POS, "block": Block.AIR}),
            ),
        )
        .state("LOCKED")
        .transition("CLOSED", "open", to="OPEN",
                    commands=(Command("say", {"text": "The door creaks open."}),))
        .transition("OPEN", "close", to="CLOSED",
                    commands=(Command("say", {"text": "The door swings shut."}),))
        .transition("CLOSED", "lock", to="LOCKED",
                    commands=(Command("playsound",
                                      {"sound": "minecraft:block.chain.place"}),))
        .transition("LOCKED", "unlock", to="CLOSED")
        .initial("CLOSED")
        .build()
    )


def furnace_machine() -> Machine[dict[str, Any]]:
    """A furnace with ``EMPTY`` / ``SMELTING`` / ``DONE`` states.

    ``insert_ore`` starts a smelt (and arms a timer score); the ``SMELTING`` state
    counts that timer down once per tick in its *cycle* loop, and the automatic
    ``finish`` transition (a ``"tick"`` event guarded by a declarative
    :class:`Condition`) fires the moment it reaches zero; ``collect`` hands the
    player a named iron ingot — the case that renders as an item *component* on
    1.20.5+ and as an NBT tag before it.
    """
    return (
        MachineBuilder[dict[str, Any]]({})
        .named("furnace")
        .for_entity(Block.FURNACE.string_id)  # type: ignore[attr-defined]
        .state("EMPTY")
        .state(
            "SMELTING",
            enter=(
                Command("say", {"text": "The furnace roars to life."}),
                Command("playsound", {"sound": "minecraft:block.furnace.fire_crackle"}),
                Command("scoreboard_set",
                        {"objective": "furnace_timer", "entry": "furnace", "value": 200}),
            ),
            # Per-tick processing loop: burn down the smelt timer each tick.
            cycle=(
                Command("scoreboard_add",
                        {"objective": "furnace_timer", "entry": "furnace", "value": -1}),
            ),
        )
        .state(
            "DONE",
            enter=(
                Command("particle", {"particle": "minecraft:flame", "pos": FURNACE_POS}),
                Command("say", {"text": "A smelt has finished."}),
            ),
        )
        .transition("EMPTY", "insert_ore", to="SMELTING",
                    commands=(Command("setblock",
                                      {"pos": FURNACE_POS, "block": Block.FURNACE,
                                       "state": {"lit": "true"}}),))
        .transition(
            # Automatic: evaluated each tick after SMELTING's cycle commands.
            "SMELTING", TICK_EVENT, to="DONE",
            condition=Condition("score_matches",
                                {"objective": "furnace_timer", "entry": "furnace",
                                 "value": 0}),
            commands=(Command("setblock",
                              {"pos": FURNACE_POS, "block": Block.FURNACE,
                               "state": {"lit": "false"}}),),
        )
        .transition(
            "DONE", "collect", to="EMPTY",
            commands=(Command("give",
                              {"target": "@p", "item": Item.IRON_INGOT, "count": 1,
                               "name": "Freshly Smelted Ingot"}),),
        )
        .initial("EMPTY")
        .build()
    )


#: Every demo machine, keyed by name — handy for iterating in examples/tests.
DEMO_MACHINES = {
    "door": door_machine,
    "furnace": furnace_machine,
}
