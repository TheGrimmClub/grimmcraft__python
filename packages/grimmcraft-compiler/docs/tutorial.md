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

The builder is designed to stay readable and typo-proof:

- `new_machine("lamp")` starts a builder — no generics, no context object.
- `add_state("OFF")` returns the state; refer to it by that **variable** in
  transitions, so a state name is written exactly once.
- effects are **methods on the state** (`on.enter.setblock(...)`,
  `on.cycle.add_score(...)`) — no effect imports, no `Command(...)` wrappers.
- the one repeated event name lives in a tiny `Event` enum.

```python
from enum import StrEnum

from grimmcraft_control import new_machine, TICK_EVENT
from grimmcraft_data import Block
from grimmcraft_core import BlockPos

LAMP_POS, TIMER = BlockPos(0, 64, 0), "lamp_timer"

class Event(StrEnum):
    PULL = "pull"

builder = new_machine("lamp")

# OFF: remove the light (set it to air) on entry.
off = builder.add_state("OFF")
off.enter.setblock(LAMP_POS, Block.AIR)

# ON: place a full-bright invisible light, click, arm a timer — one line each —
# and count the timer down every tick. light[level=15] stays lit with no power.
on = builder.add_state("ON")
on.enter.setblock(LAMP_POS, Block.LIGHT, level=15)
on.enter.playsound("minecraft:block.lever.click")
on.enter.say("The lamp glows.")
on.enter.set_score(TIMER, "lamp", 100)
on.cycle.add_score(TIMER, "lamp", -1)

# Pass the state objects (off / on) — no repeated name strings.
builder.transition(off, Event.PULL, to=on)
builder.transition(on, Event.PULL, to=off)

# Automatic: checked every tick after ON's cycle; off when the timer hits 0.
auto = builder.add_transition(on, TICK_EVENT, to=off)
auto.when_score(TIMER, "lamp", 0)

builder.initial(off)
lamp = builder.build()
```

Key ideas:

- **Effects are methods on each phase.** `state.enter`, `state.exit`,
  `state.cycle` and `transition.do` expose `.setblock(...)`, `.fill(...)`,
  `.say(...)`, `.set_score(...)`, `.if_score(...)`, … — discoverable by
  autocomplete, and you import nothing to use them.
- **One step per line.** Each call does one thing, so you can read top-to-bottom
  and edit a single step in isolation.
- **`cycle`** runs every tick while in the state; **`enter`/`exit`** fire on
  state change.
- **`TICK_EVENT`** transitions are *automatic*: checked every tick, after the
  state's cycle. Their `when_score` becomes an `execute if score …` guard.
- For a conditional inside a cycle, chain it:
  `state.cycle.if_score("stage", "tree", 1).fill(a, b, Block.OAK_LOG)`.

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
