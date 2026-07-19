# Support matrix

Detection reads the compiler's `version.py` table backwards, so this package
never carries its own version knowledge — adding a row there makes it
decompilable here.

## Versions and how they are told apart

| Version | `pack_format` | Folder scheme | Item/block data | Text components |
|---------|:-------------:|---------------|-----------------|-----------------|
| 1.20.1  | 15 | plural (`functions/`)  | NBT tags   | JSON |
| 1.20.2  | 18 | plural  | NBT tags   | JSON |
| 1.20.4  | 26 | plural  | NBT tags   | JSON |
| 1.20.5  | 41 | plural  | **components** | JSON |
| 1.20.6  | 41 | plural  | components | JSON |
| 1.21    | 48 | **singular** (`function/`) | components | JSON |
| 1.21.1  | 48 | singular | components | JSON |
| 1.21.3  | 57 | singular | components | JSON |
| 1.21.4  | 61 | singular | components | JSON |
| 1.21.5  | 71 | singular | components | **SNBT** |
| 1.21.9  | 88 | singular | components | SNBT |
| 1.21.10 | 88 | singular | components | SNBT |
| 1.21.11 | 94.1 | singular | components | SNBT |

Thresholds (data, in `version.py`):

- **Singular folders** from **1.21** (`functions` → `function`, `tags/functions`
  → `tags/function`, `loot_tables` → `loot_table`, …). The world-generation
  registries (`dimension`, `dimension_type`, `worldgen`) were *always* singular
  and are unaffected.
- **Components** from **1.20.5** (item/block data as components, not NBT tags).
- **SNBT text components** from **1.21.5** (`{text:"…"}` instead of
  `{"text":"…"}`).
- **`min_format`/`max_format`** from pack format **82** (1.21.9+), replacing
  `pack_format` + `supported_formats`.

## Detection signals

Strongest first — see `detect.py`.

| Signal | Confidence | Notes |
|--------|-----------|-------|
| Description tail: `… for <version> <flavor>` | `EXACT` | Written by `compile_machines`. The only signal that separates versions sharing a format. |
| `pack_format` / `min_format` mapping to one version | `HIGH` | |
| `pack_format` mapping to several, narrowed by folder scheme | `AMBIGUOUS` | Newest candidate assumed; `GD2003`. |
| Nothing usable | `FALLBACK` | Newest version matching the folder scheme; `GD1001`. |

Formats shared by several versions — where the description hint is what makes a
byte-identical round-trip possible:

| Format | Versions |
|-------:|----------|
| 41 | 1.20.5, 1.20.6 |
| 48 | 1.21, 1.21.1 |
| 88 | 1.21.9, 1.21.10 |

`--version` overrides all of it and is always `EXACT`.

## Flavors

| Flavor | Meaning |
|--------|---------|
| `vanilla` | Strict vanilla command set. |
| `paper` | Vanilla datapack semantics; documented Paper additions allowed. |
| `fabric` | Vanilla-compatible datapack. |

A pack records its flavor only in the description tail; otherwise `--flavor`
supplies it (default `vanilla`). Flavor never changes the folder scheme or
`pack_format`, so it cannot be inferred from the tree — but it *is* written into
`INSTALL.md`, so it must be right for a byte-identical round-trip.
