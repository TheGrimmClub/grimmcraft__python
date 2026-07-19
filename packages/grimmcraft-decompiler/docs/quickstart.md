# Quickstart

Turn an installed datapack back into the Python that could have written it.

## Install

The package is part of the workspace, so a root `task install` is enough:

```sh
task install
```

## Decompile something

Point it at a datapack folder (or a `.zip`):

```sh
grimmcraft-decompile packages/grimmcraft-compiler/examples/generated/tutorial-lamp
```

That prints builder Python:

```python
def build_lamp() -> MachineDefault:
    """Rebuild the 'lamp' machine."""
    builder = new_machine('lamp')

    off = builder.add_state('OFF')
    off.enter.setblock(BlockPos(0, 64, 0), 'minecraft:air')

    on = builder.add_state('ON')
    on.enter.setblock(BlockPos(0, 64, 0), 'minecraft:light', level='15')
    on.enter.playsound('minecraft:block.lever.click')
    on.enter.say('The lamp glows.')
    on.enter.set_score('lamp_timer', 'lamp', 100)
    on.cycle.add_score('lamp_timer', 'lamp', -1)

    builder.transition(off, 'pull', to=on)
    builder.transition(on, 'pull', to=off)
    edge_2 = builder.add_transition(on, TICK_EVENT, to=off)
    edge_2.when_score('lamp_timer', 'lamp', 0)

    builder.initial(off)
    return builder.build()
```

Run that module and it recompiles the datapack it came from.

## The three levels

```sh
grimmcraft-decompile <pack> --emit ir        # every line as a declarative Command
grimmcraft-decompile <pack> --emit machine   # the reconstructed state machines
grimmcraft-decompile <pack> --emit python    # runnable builder source (default)
```

`--emit ir` works on **any** datapack. `machine` and `python` need a pack built by
`grimmcraft-compile`; on anything else the tool says why (`GD3001`) and prints the
IR instead, rather than failing.

## Prove it round-trips

```sh
grimmcraft-decompile <pack> --roundtrip
```

Decompiles, recompiles, and diffs against the original. See
[roundtrip.md](roundtrip.md).

## Other options

| Option | Effect |
|--------|--------|
| `--output FILE` | write the result instead of printing it |
| `--version 1.21.4` | override auto-detection (needed when `pack_format` is ambiguous or unknown) |
| `--flavor paper` | set the flavor when the pack does not record one |
| `--strict` | promote warnings to errors |
| `--force` | write output even when errors are present |
| `--dry-run` | analyse and report; write nothing |
| `--list-versions` | print the supported versions |

## From Python

```python
from grimmcraft_decompiler import decompile

result = decompile("saves/world/datapacks/tutorial-lamp", emit="python")
with result.source:
    print(result.target)          # 1.21.11 vanilla
    print(result.machines[0].name)  # lamp
    print(result.output)            # the generated module
```

`result.source` holds a temporary directory when the input was a `.zip`, so use
it as a context manager (or call `result.source.close()`).

## Finding packs to decompile

`grimmcraft-world` discovers the packs installed in a world:

```python
from grimmcraft_world.world import locate_world, read_world_info

info = read_world_info(locate_world("./_input"))
for pack in info.datapacks:
    print(pack.name, pack.enabled)
```

## Tasks

```sh
task decompiler:lamp        # decompile the tutorial lamp (demo)
task decompiler:example     # decompile every committed example pack
task decompiler:roundtrip   # decompile + recompile all of them, assert equality
task decompiler:test        # the test suite
task decompiler:run -- <pack> --emit ir
```
