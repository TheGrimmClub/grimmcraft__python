#!/usr/bin/env python
"""Example: compile a machine that lays out an 8x8 chessboard of wool.

Shows generating many blocks with a plain Python loop — the machine API is just
Python. The ``BUILT`` state's ``enter`` places 64 alternating white/black wool
blocks; a ``clear`` transition sets them all back to air.

Run it (from the package dir, or via ``task compiler:chess``)::

    uv run --package grimmcraft-compiler python examples/chessboard.py
"""

# Imports
from grimmclub import StrEnum, yes, no
from grimmcraft_compiler import Target, compile_machines
from grimmcraft_control import MachineDefault, new_machine
from grimmcraft_core import BlockPos, BlockType

# Constants
ORIGIN = BlockPos(0, 64, 0)  # north-west corner of the board (col = +x, row = +z)
SIZE = 8
OUTPUT = "examples/generated/chessboard"

# Types
class Event(StrEnum):
    """The board's events (named once here, referenced by member below)."""

    BUILD = "build"
    CLEAR = "clear"

# Code
def build_chessboard() -> MachineDefault:
    """A ``chessboard`` machine: ``build`` lays the board, ``clear`` removes it."""
    builder = new_machine("chessboard")

    # add_state returns the state; keep it in a variable and refer to it below,
    # so the state names are written exactly once.
    empty = builder.add_state("EMPTY")

    # The BUILT state paints the whole 8x8 grid on entry. A square is white when
    # its (row + col) is even, black when odd — the classic checkerboard.
    built = builder.add_state("BUILT")
    built.enter.say("Placing the chessboard.")
    for row in range(SIZE):
        for col in range(SIZE):
            wool = BlockType.WHITE_WOOL if (row + col) % 2 == 0 else BlockType.BLACK_WOOL
            built.enter.setblock(ORIGIN.offset(col, 0, row), wool)

    # `build` lays the board; `clear` wipes it back to air, square by square.
    builder.transition(empty, Event.BUILD, to=built)
    clear = builder.add_transition(built, Event.CLEAR, to=empty)
    for row in range(SIZE):
        for col in range(SIZE):
            clear.do.setblock(ORIGIN.offset(col, 0, row), BlockType.AIR)

    builder.initial(empty)
    return builder.build()

# Main function
def main() -> None:
    board = build_chessboard()
    target = Target.resolve("1.21.11", "vanilla")
    result = compile_machines([board], target, namespace="chess", output=OUTPUT, DEBUG=yes)

    build_id, build_text = next(
        (fid, text) for fid, text in result.rendered().items()
        if fid.endswith("build__built")
    )
    lines = build_text.splitlines()
    print(f"\n# {build_id}  ({len(lines)} lines) — first 6:")
    print("\n".join(lines[:6]))
    print(f"Trigger in-game with: /function chess:{board.name}/on_{Event.BUILD}")

# Call main function on execution
if __name__ == "__main__":
    main()
