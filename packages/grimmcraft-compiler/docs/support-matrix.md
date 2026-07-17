# Support matrix

The `Target` (version + flavor) drives everything. All version-specific
behaviour is resolved from the data-driven table in `version.py` — add a row to
support a new version.

## Versions

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

Thresholds (also data, in `version.py`):

- **Singular folders** from **1.21** (`functions` → `function`, `tags/functions`
  → `tags/function`, `loot_tables` → `loot_table`, …).
- **Components** from **1.20.5** (item/block data as components, not NBT tags).
- **SNBT text components** from **1.21.5** (`{text:"…"}` instead of
  `{"text":"…"}`).

`pack.mcmeta` is written with `pack_format` **and** a `supported_formats`
`{min_inclusive, max_inclusive}` band.

Unknown versions fail fast with the list of supported versions.

## Flavors

| Flavor | Meaning |
|--------|---------|
| `vanilla` | Strict vanilla command set. |
| `paper` | Vanilla datapack semantics; documented Paper additions allowed. Commands flagged `requires_flavor="paper"` on a non-Paper target warn (`GC2002`). |
| `fabric` | Vanilla-compatible datapack. Commands flagged `requires_mod_api` warn (`GC2002`) — a Fabric mod, not a datapack, is needed. |

Flavor never changes the folder scheme or `pack_format`; it only changes which
commands are portable, surfaced as warnings rather than silently-invalid output.
