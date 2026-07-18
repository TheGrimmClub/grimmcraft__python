# Component reference

Every component, its family, its block, and its behaviour. Delays are in game
ticks (gt); a redstone tick (rt) is 2 gt.

## inputs — sources

| Component | Block | Behaviour | Delay |
| --- | --- | --- | --- |
| `Lever` | `lever` | toggle; strong 15 while on | 0 |
| `Button` | `stone_button` / `oak_button` | momentary strong pulse | 20 gt (stone) / 30 gt (wooden) |
| `RedstoneBlock` | `redstone_block` | constant strong 15 | 0 |
| `Observer` | `observer` | pulse on watched-cell change | 2 gt pulse |
| `PressurePlate` | `stone_pressure_plate` | strong 15 while stood on | 0 |
| `WeightedPressurePlate` | `light/heavy_weighted_pressure_plate` | analog from entity count | 0 |
| `DaylightSensor` | `daylight_detector` | analog from sky light (± inverted) | 0 |
| `AnalogSource` | (target / lectern / tripwire / detector rail) | settable analog level | 0 |

## connectors — transmission

| Component | Block | Behaviour | Delay |
| --- | --- | --- | --- |
| `RedstoneDust` | `redstone_wire` | carries power, −1 per block, 15-block range | 0 |
| `SolidBlock` | `stone` | conducts strong power; re-emits; holds torches | 0 |

## outputs — loads

| Component | Block | Behaviour | Trigger |
| --- | --- | --- | --- |
| `RedstoneLamp` | `redstone_lamp` | lit while powered | level |
| `Piston` / `StickyPiston` | `piston` / `sticky_piston` | extend/retract; push limit 12; sticky retract | level |
| `Dispenser` / `Dropper` | `dispenser` / `dropper` | fire one item | rising edge |
| `NoteBlock` | `note_block` | play note | rising edge |
| `Bell` | `bell` | ring | rising edge |
| `Hopper` | `hopper` | **locked while powered** | level |
| `Door` / `Trapdoor` / `FenceGate` | `iron_door`, … | open while powered | level |
| `Tnt` | `tnt` | primed while powered | level |
| `PoweredRail` / `ActivatorRail` | `powered_rail` / `activator_rail` | active while powered | level |

## functions — logic

| Component | Block | Behaviour | Delay |
| --- | --- | --- | --- |
| `RedstoneTorch` | `redstone_torch` | **inverter (NOT)**; burns out under rapid toggling | 1 rt |
| `Repeater` | `repeater` | one-way diode; re-emits 15; side-lock | 1–4 rt |
| `Comparator` | `comparator` | compare / subtract; reads container fullness | 1 rt |
| `Container` | `chest` | provides a 0–15 comparator reading | — |
| `NotGate` | `redstone_torch` | ¬a | 0¹ |
| `AndGate` / `OrGate` | `redstone_torch` | a∧b / a∨b | 0¹ |
| `NandGate` / `XorGate` | `redstone_torch` | ¬(a∧b) / a⊕b | 0¹ |
| `Clock` | `repeater` | oscillator; toggles every `period` gt | — |

¹ The gate components model the boolean function directly (evaluated through the
simulator) — the faithful abstraction of the primitive torch-and-dust builds. In
real redstone every gate carries the delay of the torches it is built from; the
NOT gate **is** a `RedstoneTorch`. See the [gallery](./gallery.md) for the
primitive layouts.

## Accuracy notes

- **Dust** loses exactly 1 level per block; a source's first dust is 15, and dust
  dies after 15 blocks.
- **Torch** is off exactly when its attachment block is powered, reacts after
  1 rt, and does **not** power its own attachment (so a floor torch is stable).
  Burnout trips after >8 flips in 60 gt, recovering after a cool-down.
- **Repeater** reads only its back face, always outputs 15, and freezes when a
  powered diode faces its side (lock).
- **Comparator** compare mode passes the back signal unless a side exceeds it;
  subtract mode outputs `back − side` floored at 0; a `Container` behind it is
  read as fullness.
- **Quasi-connectivity** (Java BUD) is opt-in per component — see
  [overview](./overview.md#java-vs-bedrock-quasi-connectivity-bud).
