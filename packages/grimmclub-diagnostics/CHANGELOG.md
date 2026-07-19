# Changelog — grimmclub-diagnostics

## feat(diagnostics): one implementation, lifted out of the compiler

The `Severity` / `Code` / `Diagnostic` / `DiagnosticBag` machinery existed
twice: once in `grimmcraft-compiler` (which `grimmcraft-decompiler` imported
from) and once, near-identically, in `grimmcraft-redstone`. The two differed in
exactly one field. It now lives here, and the three packages keep only their own
catalogues — 32 codes across `GC####`, `GD####` and `RS####`.

**Nothing here knows what a code means.** That is the point: it is what lets a
single explanation layer (`grimmclub-mentor`) teach from every producer without
special-casing each one.

Two fields describe *where*, because the domains could not agree with one:

- `source` — a human label, and the only one rendered ("door--open-->OPEN",
  "pack.mcfunction:12", "(3, 1, 2)").
- `location` — the structured original when there is one, deliberately untyped
  so this package never learns about anyone's coordinate class. Redstone keeps
  its `BlockPos` here rather than having it flattened to a string, so a tool can
  still jump to the fault.

`report()` now takes an optional console and returns the plain text either way.
The compiler printed through rich; redstone returned a string. Both are
legitimate — a diagnostics system is used to show a person something *and* to
assert on it in a test — so both are supported rather than one being converted.
