# Tutorial — build a machine and compile it

This walks through [`examples/tutorial_lamp.py`](../examples/tutorial_lamp.py):
a redstone lamp built from scratch, then compiled to a datapack. Run it with:

```bash
uv run --package grimmcraft-compiler python examples/tutorial_lamp.py
```

## 1. The machine

A lamp has two states, `OFF` and `ON`, toggled by a `pull` event. Turning `ON`
lights the block, clicks, and arms a 100-tick timer; a per-tick **cycle** counts
that timer down, and an automatic transition switches back `OFF` at zero.

```python
from grimmcraft_control.machine import Command, Condition, MachineBuilder, TICK_EVENT
from grimmcraft_data import Block
from grimmcraft_core import BlockPos

LAMP_POS, TIMER = BlockPos(0, 64, 0), "lamp_timer"

lamp = (
    MachineBuilder[dict]({})
    .named("lamp")
    .state("OFF", enter=(
        Command("setblock", {"pos": LAMP_POS, "block": Block.REDSTONE_LAMP,
                             "state": {"lit": "false"}}),
    ))
    .state("ON",
        enter=(
            Command("setblock", {"pos": LAMP_POS, "block": Block.REDSTONE_LAMP,
                                 "state": {"lit": "true"}}),
            Command("playsound", {"sound": "minecraft:block.lever.click"}),
            Command("scoreboard_set", {"objective": TIMER, "entry": "lamp", "value": 100}),
        ),
        cycle=(  # runs every tick while ON
            Command("scoreboard_add", {"objective": TIMER, "entry": "lamp", "value": -1}),
        ),
    )
    .transition("OFF", "pull", to="ON")
    .transition("ON", "pull", to="OFF")
    .transition("ON", TICK_EVENT, to="OFF",   # automatic, checked after the cycle
                condition=Condition("score_matches",
                                    {"objective": TIMER, "entry": "lamp", "value": 0}))
    .initial("OFF")
    .build()
)
```

Key ideas:

- **`enter` / `exit` / `cycle`** are tuples of declarative `Command`s. `enter`
  and `exit` fire on state change; `cycle` runs every tick while in the state.
- Using **`Block.REDSTONE_LAMP`** (a `grimmcraft-data` enum member) instead of a
  raw string means the id is valid by construction — the compiler never has to
  guess or warn.
- **`TICK_EVENT`** transitions are *automatic*: the compiler checks them every
  tick, after the state's cycle commands. Their `Condition` becomes an
  `execute if score …` guard.

## 2. Compile it

```python
from grimmcraft_compiler import Target, compile_machines

target = Target.resolve("1.21.1", "vanilla")
result = compile_machines([lamp], target, namespace="tutorial",
                          output="dist/tutorial-lamp")
assert result.ok
```

## 3. What comes out

Each part of the machine lowers to a function:

**`tutorial:lamp/init`** — sets the starting state and runs `OFF`'s enter commands
(called from the pack's `load`):

```mcfunction
# states: OFF=0, ON=1
scoreboard players set lamp grimmcraft_state 0
setblock 0 64 0 minecraft:redstone_lamp[lit=false]
```

**`tutorial:lamp/on_pull`** — the event trigger; dispatches to the transition for
whichever state currently holds:

```mcfunction
execute if score lamp grimmcraft_state matches 0 run function tutorial:lamp/do_off__pull__on
execute if score lamp grimmcraft_state matches 1 run function tutorial:lamp/do_on__pull__off
```

**`tutorial:lamp/do_off__pull__on`** — a transition: exit → commands → state
write → enter:

```mcfunction
scoreboard players set lamp grimmcraft_state 1
setblock 0 64 0 minecraft:redstone_lamp[lit=true]
playsound minecraft:block.lever.click master @a
scoreboard players set lamp lamp_timer 100
```

**`tutorial:lamp/tick` → `tutorial:lamp/tick_on`** — the per-tick loop: cycle
commands first, then the automatic transition's guard:

```mcfunction
# tick dispatches by state:
execute if score lamp grimmcraft_state matches 1 run function tutorial:lamp/tick_on
# tick_on:
scoreboard players add lamp lamp_timer -1
execute if score lamp lamp_timer matches 0 run function tutorial:lamp/do_on__tick__off
```

**`tutorial:load` / `tutorial:tick`** — the pack hooks (registered in
`minecraft:load` / `minecraft:tick`): declare the objectives and call each
machine's `init` / `tick`.

## 4. Install and try it

Copy `dist/tutorial-lamp/` into `saves/<world>/datapacks/`, `/reload`, then:

```
/function tutorial:lamp/on_pull      # toggle the lamp
/scoreboard objectives setdisplay sidebar grimmcraft_state
```

Pull it on and watch the lamp turn itself off ~5 seconds (100 ticks) later — the
cycle + automatic transition at work, with no further commands from you.

## Next steps

- Change the target to `1.20.4` and re-run: the folder scheme becomes plural and
  item data would render as NBT (see [support-matrix.md](support-matrix.md)).
- Add a second machine and compile them together — they share one `grimmcraft_state`
  objective and one `load`/`tick` (see [`examples/compile_demos.py`](../examples/compile_demos.py)).
- Reference a bad id on purpose and read the diagnostic (see
  [diagnostics.md](diagnostics.md)).
```
