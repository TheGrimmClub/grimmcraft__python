# Diagnostics

`analyze(circuit)` runs a bounded simulation and inspects the result, returning a
`DiagnosticBag`. Each `Diagnostic` says **what** is wrong, **where** (a
`BlockPos`), and **how** to fix it, under a stable `RS####` code.

```python
from grimmcraft_redstone import Circuit, RedstoneLamp, analyze
from grimmcraft_core.coordinates import BlockPos

circuit = Circuit()
circuit.place(RedstoneLamp(BlockPos(5, 0, 0)))   # nothing powers it
print(analyze(circuit).report())
# warning RS2002: RedstoneLamp is never powered during simulation
#     at (5, 0, 0)
#     hint: connect it to a power source via dust, a block, or a diode
```

## Codes

| Code | Severity | Meaning |
| --- | --- | --- |
| `RS1001` | error | a diode (repeater) is wired to nothing on its input face |
| `RS2001` | warning | a component is never powered during simulation |
| `RS2002` | warning | a load can never activate |
| `RS2003` | warning | a comparator does not read a container behind it |
| `RS2004` | warning | a redstone torch is on an invalid attachment block |
| `RS2005` | warning | the circuit never stabilised — a likely (unintended) clock |

`DiagnosticBag` exposes `.errors`, `.warnings`, `.has_errors`, `.of(severity)`,
and `.report()` for a grouped plain-text summary.
