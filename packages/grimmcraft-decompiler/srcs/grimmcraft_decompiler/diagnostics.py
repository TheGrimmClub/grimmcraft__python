"""The decompiler's diagnostic codes — the ``GD####`` range.

The machinery (:class:`~grimmcraft_compiler.diagnostics.Diagnostic`,
:class:`DiagnosticBag`, :class:`Severity`, :class:`Code`) is **reused verbatim**
from the compiler; only the catalogue is new, so a decompile report reads exactly
like a compile report and the two can share one bag.

``source`` on a decompiler diagnostic is a *file position* — ``"<file>:<line>"``
— rather than the compiler's machine/transition path, since the input here is
text on disk.
"""

from __future__ import annotations

from grimmcraft_compiler.diagnostics import (
    Code,
    Diagnostic,
    DiagnosticBag,
    Severity,
)

__all__ = ["Code", "Codes", "Diagnostic", "DiagnosticBag", "Severity", "at"]


def at(file: str, line: int | None = None) -> str:
    """Format a diagnostic ``source`` as ``file`` or ``file:line``."""
    return file if line is None else f"{file}:{line}"


class Codes:
    """The catalogue of every diagnostic the decompiler can emit.

    Ranges mirror the compiler's: ``GD1###`` errors, ``GD2###`` warnings,
    ``GD3###`` info.
    """

    # --- errors --------------------------------------------------------------
    UNKNOWN_PACK_FORMAT = Code("GD1001", "Unknown pack format", Severity.ERROR)
    MISSING_PACK_MCMETA = Code("GD1002", "Missing or invalid pack.mcmeta", Severity.ERROR)
    UNKNOWN_ID = Code("GD1003", "Unknown registry id", Severity.ERROR)
    NO_DATA_DIRECTORY = Code("GD1004", "Datapack has no data/ directory", Severity.ERROR)
    ROUNDTRIP_MISMATCH = Code("GD1005", "Round-trip produced a different pack", Severity.ERROR)

    # --- warnings ------------------------------------------------------------
    FOLDER_SCHEME_MISMATCH = Code(
        "GD2001", "Folder scheme disagrees with pack_format", Severity.WARNING
    )
    UNPARSEABLE_COMMAND = Code("GD2002", "Unrecognised command line", Severity.WARNING)
    AMBIGUOUS_VERSION = Code("GD2003", "Ambiguous version detection", Severity.WARNING)
    AMBIGUOUS_RECONSTRUCTION = Code(
        "GD2004", "Ambiguous machine reconstruction", Severity.WARNING
    )
    DATA_MODEL_MISMATCH = Code(
        "GD2005", "Item data model disagrees with the detected version", Severity.WARNING
    )
    DEPRECATED_ID = Code("GD2006", "Deprecated id", Severity.WARNING)
    AMBIGUOUS_NAMESPACE = Code("GD2007", "Ambiguous pack namespace", Severity.WARNING)

    # --- info ----------------------------------------------------------------
    NOT_LIFTABLE = Code("GD3001", "Not liftable to a machine", Severity.INFO)
    STATS = Code("GD3002", "Decompilation summary", Severity.INFO)

    @classmethod
    def all(cls) -> list[Code]:
        """Every registered code, in id order."""
        codes = [v for v in vars(cls).values() if isinstance(v, Code)]
        return sorted(codes, key=lambda c: c.id)
