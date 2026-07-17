#!/usr/bin/env python
"""Example: compile a machine that lays out an 8x8 chessboard of wool.

This shows generating *many* blocks with a plain Python loop — the machine API is
just Python, so you build commands however you like. The ``BUILT`` state's
``on_enter`` places 64 alternating white/black wool blocks; a ``clear`` transition
sets them all back to air.

Run it::

    uv run --package grimmcraft-compiler python examples/chessboard.py
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from grimmcraft_compiler import Target, compile_machines
from grimmcraft_compiler.dialect import Dialect
from grimmcraft_compiler.emit import render_function
from grimmcraft_control.machine import Machine, MachineBuilder, say, setblock
from grimmcraft_core import BlockPos
from grimmcraft_data import Block

ORIGIN = BlockPos(0, 64, 0)  # north-west corner of the board (col = +x, row = +z)
SIZE = 8
GENERATED = Path(__file__).resolve().parent / "generated"


def build_chessboard() -> Machine[dict[str, Any]]:
    """A ``chessboard`` machine: ``build`` lays the board, ``clear`` removes it."""
    builder = MachineBuilder[dict[str, Any]]({})
    builder.named("chessboard")

    builder.add_state("EMPTY")

    # The BUILT state paints the whole 8x8 grid on entry. A square is white when
    # its (row + col) is even, black when odd — the classic checkerboard.
    built = builder.add_state("BUILT")
    built.on_enter(say("Placing the chessboard."))
    for row in range(SIZE):
        for col in range(SIZE):
            wool = Block.WHITE_WOOL if (row + col) % 2 == 0 else Block.BLACK_WOOL
            built.on_enter(setblock(ORIGIN.offset(col, 0, row), wool))

    # `build` lays the board; `clear` wipes it back to air, square by square.
    builder.transition("EMPTY", "build", to="BUILT")
    clear = builder.add_transition("BUILT", "clear", to="EMPTY")
    for row in range(SIZE):
        for col in range(SIZE):
            clear.do(setblock(ORIGIN.offset(col, 0, row), Block.AIR))

    builder.initial("EMPTY")
    return builder.build()


def main() -> None:
    board = build_chessboard()
    target = Target.resolve("1.21.1", "vanilla")
    result = compile_machines(
        [board], target, namespace="chess", output=GENERATED / "chessboard"
    )

    print(f"target    : {target}")
    print(f"ok        : {result.ok}")
    print(f"functions : {len(result.pack.functions)}")
    print(f"output    : {result.output_path}")

    # Show the first few lines of the 64-block build function.
    dialect = Dialect(target)
    build_fn = next(
        f for f in result.pack.functions if f.id.path.endswith("build__built")
    )
    lines = render_function(build_fn, dialect).splitlines()
    print(f"\n# {build_fn.id}  ({len(lines)} lines) — first 6:")
    print("\n".join(lines[:6]))
    print(f"Trigger in-game with: /function chess:{board.name}/on_build")


if __name__ == "__main__":
    main()
