"""The compiler's diagnostic catalogue — the ``GC####`` codes.

The machinery (:class:`Severity`, :class:`Code`, :class:`Diagnostic`,
:class:`DiagnosticBag`) lives in ``grimmclub-diagnostics`` and is re-exported
here, so existing imports keep working and this module holds only what is
actually specific to compiling: which problems the compiler can report.
"""

from __future__ import annotations

from grimmclub_diagnostics import Code, Diagnostic, DiagnosticBag, Severity

__all__ = ["Code", "Codes", "Diagnostic", "DiagnosticBag", "Severity"]


# --- the code registry (also the source for docs/diagnostics.md) -------------
class Codes:
    """The catalogue of every diagnostic the compiler can emit."""

    UNKNOWN_ID = Code("GC1001", "Unknown registry id", Severity.ERROR)
    INVALID_RESOURCE_LOCATION = Code(
        "GC1002", "Invalid resource location", Severity.ERROR
    )
    UNRESOLVED_FUNCTION = Code("GC1003", "Unresolved function reference", Severity.ERROR)
    UNRESOLVED_TAG_MEMBER = Code(
        "GC1004", "Unresolved function-tag member", Severity.ERROR
    )
    UNAVAILABLE_FEATURE = Code(
        "GC1005", "Feature unavailable in target version", Severity.ERROR
    )
    UNKNOWN_COMMAND = Code("GC1006", "Unknown command (cannot lower)", Severity.ERROR)
    DEPRECATED_ID = Code("GC2001", "Deprecated id", Severity.WARNING)
    FLAVOR_MISMATCH = Code("GC2002", "Command not portable to this flavor",
                           Severity.WARNING)
    NON_COMPILABLE_GUARD = Code(
        "GC2003", "Runtime guard cannot be compiled", Severity.WARNING
    )
    EMPTY_MACHINE = Code("GC2004", "Machine has no transitions", Severity.WARNING)
    STATS = Code("GC3001", "Compilation summary", Severity.INFO)
    VERIFY_FAILED = Code("GC4001", "Output verification failed", Severity.ERROR)

    @classmethod
    def all(cls) -> list[Code]:
        """Every registered code, in id order."""
        codes = [v for v in vars(cls).values() if isinstance(v, Code)]
        return sorted(codes, key=lambda c: c.id)
