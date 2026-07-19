"""grimmcraft-decompiler — lift Minecraft datapacks back into grimmcraft machines.

The inverse of ``grimmcraft-compiler``, in three levels that degrade into each
other:

1. **IR** — every ``.mcfunction`` line back into a declarative ``Command``, plus
   tags and resources.  Works on *any* datapack; anything the IR cannot model is
   preserved verbatim as a ``raw`` command, so nothing is ever lost.
2. **Machine** — recognise the grimmcraft lowering conventions in that IR and
   rebuild the :class:`~grimmcraft_control.machine.Machine` objects behind it.
3. **Python** — emit runnable builder source that recreates those machines.

Everything version-specific is resolved from the compiler's own support table and
:class:`~grimmcraft_compiler.dialect.Dialect`; the reader is that dialect run
backwards, and each parse is verified by re-rendering it.  Hence the round-trip
contract: for any pack the compiler produced, re-emitting the decompiled result
reproduces it byte for byte (:func:`~grimmcraft_decompiler.roundtrip.roundtrip`).

    from grimmcraft_decompiler import decompile

    result = decompile("saves/world/datapacks/tutorial-lamp", emit="python")
    print(result.output)
"""

from __future__ import annotations

from grimmcraft_decompiler.codegen import generate_python
from grimmcraft_decompiler.decompiler import EMIT_LEVELS, DecompileResult, decompile
from grimmcraft_decompiler.detect import Confidence, Detection, detect_target
from grimmcraft_decompiler.diagnostics import (
    Code,
    Codes,
    Diagnostic,
    DiagnosticBag,
    Severity,
)
from grimmcraft_decompiler.lift_ir import lift_ir, render_ir
from grimmcraft_decompiler.lift_machine import lift_machines, machine_names
from grimmcraft_decompiler.reader import CommandReader
from grimmcraft_decompiler.roundtrip import DiffReport, FileDiff, Level, roundtrip
from grimmcraft_decompiler.source import PackSource, open_pack

__all__ = [
    "decompile",
    "DecompileResult",
    "EMIT_LEVELS",
    "open_pack",
    "PackSource",
    "detect_target",
    "Detection",
    "Confidence",
    "CommandReader",
    "lift_ir",
    "render_ir",
    "lift_machines",
    "machine_names",
    "generate_python",
    "roundtrip",
    "DiffReport",
    "FileDiff",
    "Level",
    "Diagnostic",
    "DiagnosticBag",
    "Severity",
    "Code",
    "Codes",
]
