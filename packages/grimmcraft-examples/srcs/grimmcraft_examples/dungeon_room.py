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
def write_region(path: Path, chunk: dict[str, object], chunk_x: int = 0,
                 chunk_z: int = 0) -> Path:
    """Write one chunk into an Anvil region file.

    Spelled out here rather than imported so the example is self-contained: it
    demonstrates the *shape* of the format capture() reads, which is worth
    seeing when you are learning what a region file is.
    """
    import zlib

    from grimmcraft_world import nbt
    from grimmcraft_world.region import SECTOR

    payload = zlib.compress(nbt.dump(chunk, gzipped=False))
    block = bytearray()
    block += (len(payload) + 1).to_bytes(4, "big")
    block += b"\x02"  # compression scheme 2 = zlib
    block += payload
    used = (len(block) + SECTOR - 1) // SECTOR       # pad to whole 4 KiB sectors
    block += b"\x00" * (used * SECTOR - len(block))

    header = bytearray(SECTOR * 2)                   # location + timestamp tables
    index = (chunk_x & 31) + (chunk_z & 31) * 32
    header[index * 4 : index * 4 + 3] = (2).to_bytes(3, "big")
    header[index * 4 + 3] = used

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(bytes(header) + bytes(block))
    return path


def build_chunk(palette: list[dict[str, object]], indices: list[int]) -> dict[str, object]:
    """A 1.18+ chunk whose section Y=4 (world y 64..79) holds ``indices``.

    Block states are bit-packed the 1.16+ way: entries never straddle two longs.
    """
    from grimmcraft_world import nbt

    bits = max(4, (len(palette) - 1).bit_length())
    per_long = 64 // bits
    longs: list[int] = []
    for start in range(0, 4096, per_long):
        packed = 0
        for slot, index in enumerate(indices[start : start + per_long]):
            packed |= (index & ((1 << bits) - 1)) << (slot * bits)
        longs.append(packed - (1 << 64) if packed >= (1 << 63) else packed)

    return {
        "DataVersion": 4189,
        "xPos": 0,
        "zPos": 0,
        "sections": [
            {"Y": 4, "block_states": {"palette": palette, "data": nbt.LongArray(longs)}}
        ],
        "block_entities": [],
    }


def make_world(root: Path) -> Path:
    """Synthesise a tiny saved world so this example is self-contained."""
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

    write_region(root / "region" / "r.0.0.mca", build_chunk(palette, indices))
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
    if result.output_path is None:
        # compile_machines emits nothing when validation found errors; there is
        # no tree to drop the structure files into, so stop and say why.
        print("  compilation produced no pack:")
        for diagnostic in result.diagnostics.errors:
            print(f"    {diagnostic.code}: {diagnostic.message}")
        return

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
