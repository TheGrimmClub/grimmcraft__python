"""grimmcraft-compiler — lower grimmcraft state machines into Minecraft datapacks.

Pipeline: **collect** machines → build a dialect-independent **IR** → **validate**
against ``grimmcraft-data`` for a :class:`Target` → **render** each command with
the version :class:`Dialect` → **emit** the datapack tree → **verify** it.  The
entry point is :func:`compile_machines`; diagnostics are first-class
(:class:`DiagnosticBag`).
"""

from __future__ import annotations

from grimmcraft_compiler.compiler import CompileResult, compile_machines, show_info
from grimmcraft_compiler.diagnostics import (
    Code,
    Codes,
    Diagnostic,
    DiagnosticBag,
    Severity,
)
from grimmcraft_compiler.dialect import Dialect
from grimmcraft_compiler.ir import (
    Datapack,
    Function,
    FunctionTag,
    Resource,
    ResourceLocation,
)
from grimmcraft_compiler.lower import lower
from grimmcraft_compiler.target import Flavor, Target
from grimmcraft_compiler.version import (
    VersionInfo,
    resolve_version,
    supported_versions,
)

__all__ = [
    "compile_machines",
    "CompileResult",
    "show_info",
    "Target",
    "Flavor",
    "Dialect",
    "lower",
    "Datapack",
    "Function",
    "FunctionTag",
    "Resource",
    "ResourceLocation",
    "VersionInfo",
    "resolve_version",
    "supported_versions",
    "Diagnostic",
    "DiagnosticBag",
    "Severity",
    "Code",
    "Codes",
]
