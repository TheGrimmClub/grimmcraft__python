# grimmcraft-redstone — model overview

Redstone is modelled as a **spatial graph of components** driven by a
**tick-based simulator**. This document covers the signal model, the four
component families, the update-order contract, and the Java/Bedrock differences.

## Signal model

A [`Signal`](../srcs/grimmcraft_redstone/signal.py) is a value object with two
parts:

- a **power level** — an integer `0..15` (`PowerLevel`), clamped on construction;
- a **kind** — `PowerKind.NONE | WEAK | STRONG`.

```python
Signal.strong(15)        # a full-strength strong source (lever, torch, diode)
Signal.weak(9)           # dust / passive weak power
Signal.off()             # level 0, kind NONE
sig.attenuate(1)         # lose one level per block (always becomes WEAK)
sig.is_on, sig.is_strong # queries
```

**Strong vs weak.** A *strong* signal powers a solid block, which then re-emits
power to everything adjacent (this is how power crosses from a repeater into a
wire on the far side of a block). A *weak* signal — redstone dust, most passive
sources — powers directly-wired components but is **not** re-emitted through a
block. `max()` on two signals picks the higher level, and strong beats weak on a
tie.

## Timing

The engine's clock counts **game ticks** (20 per second). A **redstone tick is
two game ticks** (0.1 s). Delays are expressed accordingly:

| Thing | Delay |
| --- | --- |
| Redstone tick | 2 game ticks |
| Repeater | 1–4 **redstone** ticks (2–8 gt), adjustable |
| Comparator | 1 redstone tick (2 gt) |
| Redstone torch | 1 redstone tick (2 gt) reaction |
| Observer pulse | 2 game ticks |
| Button (stone / wooden) | 20 / 30 game ticks |

Use `redstone_ticks(n)` to convert.

## The four families

| Family | Role | Package | Examples |
| --- | --- | --- | --- |
| **inputs** | originate power | `inputs/` | lever, button, redstone block, observer, pressure plates, daylight sensor |
| **connectors** | transmit power | `connectors/` | redstone dust, solid block |
| **outputs** | consume power (loads) | `outputs/` | lamp, piston, dispenser, hopper, note block, door, TNT, rails, bell |
| **functions** | logic | `functions/` | torch (NOT), repeater, comparator, gates, clock |

Every component is a `RedstoneComponent` with a `position`, a `facing`
`Direction`, and a `block_type` `Block` (from `grimmcraft-data`). Behaviour is
three methods — `output_signal()`, `inputs()`, `update(ctx, tick)` — and the
structural roles are the `PowerSource` / `Conductor` / `Load` / `LogicGate`
protocols.

Placement reuses `grimmcraft-core`: positions are `BlockPos`, facing/orientation
is `Direction`.

## Update-order contract (determinism)

Redstone is order-sensitive, so the engine fixes a scheme and states it:

1. Each `Simulator.step()` advances the world by **one game tick**.
2. A step is **synchronous**: it first snapshots every component's published
   output, then resolves the dust power field from that snapshot, then evaluates
   every component **against the frozen snapshot**. No component observes
   another's *new* output within the same tick, so the result is **independent of
   evaluation order**.
3. Where an order is still visible (change reporting, tie-breaks) components are
   visited in ascending `(x, y, z)` position order.
4. Consequence: signals propagate **one component-hop per tick**; only redstone
   dust is resolved globally (instantly) each tick, so a long dust line reaches
   full length in a single tick.

`run_until_stable(max_ticks)` steps until the whole-world state repeats — a
**fixpoint** (stable) or a previously seen state (a **cycle** → oscillating). It
never loops forever; a clock is reported, not hung.

## Diagnostics

`analyze(circuit)` returns a `DiagnosticBag` of stable `RS####` codes with a
location and a fix hint. It reports: floating / never-powered components and
loads, comparators that read no container, torches on an invalid attachment,
diodes wired to nothing, and likely-unintended oscillation. See
[`diagnostics.md`](./diagnostics.md).

## Java vs Bedrock: quasi-connectivity (BUD)

**Quasi-connectivity** — a piston/dispenser/dropper being powered *through* the
block one above it — is a **Java-only** behaviour and differs from Bedrock. It is
**off by default** (Bedrock-like) and enabled per-component:

```python
Piston(pos, facing=Direction.UP, quasi_connectivity=True)  # Java BUD behaviour
```

This is the only intentional flavour difference the model exposes; everything
else follows Java Edition 1.21.
