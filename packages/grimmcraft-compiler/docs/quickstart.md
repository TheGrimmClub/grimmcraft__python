# Quickstart

## Install / sync

```bash
uv sync --all-packages
```

## Compile from the CLI

```bash
# Door + Furnace demos, 1.21.11 vanilla, into dist/grimmcraft/
uv run grimmcraft-compile --version 1.21.11 --flavor vanilla

# Pick one machine, a namespace and an output dir; also zip it
uv run grimmcraft-compile --machine furnace --namespace mypack \
    --output dist/mypack --zip

# Validate only (emit nothing), warnings as errors
uv run grimmcraft-compile --version 1.20.4 --dry-run --strict

# What versions are supported?
uv run grimmcraft-compile --list-versions
```

Also runnable as `python -m grimmcraft_compiler`. The command exits non-zero when
there are errors.

## Compile from Python

```python
from pathlib import Path
from grimmcraft_compiler import Target, compile_machines
from grimmcraft_control.demos import door_machine, furnace_machine

target = Target.resolve("1.21.11", "vanilla")
result = compile_machines(
    [door_machine(), furnace_machine()],
    target,
    namespace="grimmcraft",
    output=Path("dist/grimmcraft"),
)

if result.ok:
    print("wrote", result.output_path)
else:
    for d in result.diagnostics.errors:
        print(d.code.id, d.message)
```

## Install the datapack in Minecraft

1. Copy the output folder (or `.zip`) into `saves/<world>/datapacks/` (or a
   server's `world/datapacks/`).
2. Run `/reload` in-game.
3. `/datapack list` should show your namespace.

The generated `INSTALL.md` inside the pack lists the exact trigger commands, e.g.
`/function grimmcraft:door/on_open`. State is tracked in the `grimmcraft_state`
scoreboard objective:

```
/scoreboard objectives setdisplay sidebar grimmcraft_state
```

## Write your own machine

Build a machine with the `grimmcraft-control` DSL, attach declarative commands,
and pass it to `compile_machines`:

```python
from grimmcraft_control.machine import Command, MachineBuilder

lamp = (
    MachineBuilder[dict]({})
    .named("lamp")
    .state("OFF")
    .state("ON", enter=(Command("say", {"text": "lit!"}),))
    .transition("OFF", "toggle", to="ON")
    .transition("ON", "toggle", to="OFF")
    .initial("OFF")
    .build()
)
```

See [architecture.md](architecture.md) for how each part becomes a function, and
[diagnostics.md](diagnostics.md) for the error codes.
