#!/usr/bin/env python
"""Save a room from a world, then build a datapack that places it.

The full loop this package exists for:

1. **capture** a box of blocks out of a saved world (no server needed),
2. **store** it as a ``.nbt`` template in a datapack,
3. **place** it from a state machine — and show that the result decompiles back
   to the same ``place`` effect.

The world here is synthesised so the example runs anywhere; point ``WORLD`` at a
real save to capture your own build.

Run it (from the package dir, or via ``task structures:example``)::

    uv run --package grimmcraft-structures python examples/dungeon_room.py
"""

# Imports
from pathlib import Path

from grimmclub import banner, no
from grimmcraft_compiler import Target, compile_machines
from grimmcraft_control import MachineDefault, new_machine
from grimmcraft_core import BlockPos
from grimmcraft_structures import Structure, StructureLibrary, capture

# Constants
NAMESPACE = "dungeon"
OUTPUT = Path("dist/dungeon")
ROOM_AT = BlockPos(0, 64, 0)


# Code
def make_world(root: Path) -> Path:
    """Synthesise a tiny saved world so this example is self-contained."""
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tests"))
    from conftest import build_chunk, write_region  # the test fixture helpers
    from grimmcraft_world import nbt

    palette: list[dict[str, object]] = [
        {"Name": "minecraft:air"},
        {"Name": "minecraft:cobblestone"},
        {"Name": "minecraft:oak_log", "Properties": {"axis": "y"}},
    ]
    indices = [0] * 4096

    def cell(x: int, y: int, z: int) -> int:
        return (y & 15) * 256 + (z & 15) * 16 + (x & 15)

    for x in range(5):  # a 5x5 cobblestone floor with oak pillars at its corners
        for z in range(5):
            indices[cell(x, 64, z)] = 1
    for corner in ((0, 0), (0, 4), (4, 0), (4, 4)):
        for y in (65, 66):
            indices[cell(corner[0], y, corner[1])] = 2

    write_region(root / "region" / "r.0.0.mca", {(0, 0): build_chunk(0, 0, palette, indices)})
    (root / "level.dat").write_bytes(nbt.dump({"Data": {"LevelName": "demo"}}))
    return root


def build_machine(room_id: str) -> MachineDefault:
    """A machine that places the room when built, and clears it again."""
    builder = new_machine("dungeon")

    with builder.add_state("EMPTY") as empty:
        empty.enter.say("The dungeon is empty.")

    with builder.add_state("BUILT") as built:
        built.enter.place(room_id, ROOM_AT)
        built.enter.say("A room appears!")

    builder.transition(empty, "build", to=built)
    builder.transition(built, "clear", to=empty)
    builder.initial(empty)
    return builder.build()


# Main function
def main() -> None:
    banner("1. capture a room out of a saved world")
    world = make_world(OUTPUT.parent / "demo-world")
    room = capture(world, BlockPos(0, 64, 0), BlockPos(4, 66, 4))
    print(f"  captured {len(room)} block(s), {room.size[0]}x{room.size[1]}x{room.size[2]}")
    for state in room.palette:
        print(f"    {state}")

    banner("2. store it as a datapack structure")
    library = StructureLibrary(NAMESPACE)
    room_id = library.add("room", room)
    print(f"  id: {room_id}")

    banner("3. place it from a machine")
    target = Target.resolve("1.21.11", "vanilla")
    result = compile_machines(
        [build_machine(room_id)], target, namespace=NAMESPACE, output=OUTPUT, DEBUG=no
    )
    written = library.write_into(result.output_path)
    for path in written:
        print(f"  wrote {path}")
    print()
    for function_id, text in result.rendered().items():
        if "place template" in text:
            print(f"# ---- {function_id} ----")
            print(text.rstrip())

    banner("4. the structure file reads back")
    restored = Structure.read(written[0])
    print(f"  {len(restored)} block(s), palette: {[str(s) for s in restored.palette]}")

    banner("5. and the pack decompiles to the same effect")
    from grimmcraft_decompiler import decompile

    decompiled = decompile(OUTPUT, emit="python")
    with decompiled.source:
        for line in decompiled.output.splitlines():
            if ".place(" in line:
                print(f"  {line.strip()}")


# Call main when script is executed
if __name__ == "__main__":
    main()
