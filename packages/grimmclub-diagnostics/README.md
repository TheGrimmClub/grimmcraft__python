# grimmclub-diagnostics

Stable diagnostic codes, severities and readable reports — the machinery behind
every `GC####` / `GD####` / `RS####` message in this workspace.

Domain-agnostic by design: each package declares its own catalogue, and nothing
here knows what any code means. That is what lets `grimmclub-mentor` explain
all of them without special-casing each producer.
