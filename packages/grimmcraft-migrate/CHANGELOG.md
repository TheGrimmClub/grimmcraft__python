# Changelog — grimmcraft-migrate

## feat(migrate): migrate command strings from 1.19 to 1.21 syntax

New package, under `srcs/grimmcraft_migrate/`. Migrates command-block commands extracted from Anvil region files into an inventory.

**Standard library only** — no dependencies at all, `argparse` rather than `click`, `unittest` rather than `pytest` — so it can be lifted out of the workspace and run on a bare Python 3.12. It is still a workspace member, so CI covers it and pytest collects its tests alongside everything else.

### What it migrates
| Change | Version |
|---|---|
| Item NBT → data components (`sword{Enchantments:…}` → `sword[minecraft:enchantments=…]`) | 1.20.5 |
| Nested item schema (`Count`/`tag` → `count`/`components`) | 1.20.5 |
| Sign text (`Text1`…`Text4` → `front_text.messages`) | 1.20 |
| Attribute renames (`generic.movement_speed` → `minecraft:movement_speed`) | 1.20.5 / 1.21.2 |
| Block positions (`{X:1,Y:2,Z:3}` → `[I;1,2,3]`) | 1.20.5 |

Text components are deliberately **not** rewritten: legacy JSON strings are still parsed by 1.21, so converting them would change bytes without changing behaviour.

### Modules
- `classify.py` — the classifier pass, run first: frequency by command name (grouping `execute … run <verb>` by its *inner* command) and by legacy shape, so effort goes to the rules the corpus actually needs. The only pass where regular expressions are appropriate, since a miscount is harmless.
- `snbt.py` — a real tokenizer and parser (compound, list, typed array, quoted/bare string, numeric suffixes). Nodes remember *how* a value was written: `5s` keeps its short suffix, a single-quoted string keeps its quotes. Two reasons — untouched values must re-serialise exactly, or a second run would churn the file; and `lvl:5s` (short) and `lvl:5` (int) are different NBT types.
- `rules.py` — the explicit mapping table, one entry per legacy key with the component it becomes and a function that rewrites the *value*, plus the attribute rename table.
- `migrate.py` — the transformation.
- `inventory.py` — read/write text or JSON, detected by content rather than extension; coordinates survive the round trip.
- `report.py` — the Markdown report.
- `verify.py` — the verification datapack.
- `cli.py` — `classify`, `migrate`, `verify`.

### Four properties, by construction
- **Nothing is dropped.** A legacy key with no mapping moves into `minecraft:custom_data` and is listed in the report — what the game itself does with data it does not recognise.
- **Idempotent.** Each pass tests for the *legacy* shape before acting, so modern input matches nothing and a second run is a no-op. Asserted over every rule.
- **Fails loudly.** A command whose NBT will not parse is reported with the reason and left **completely** unchanged — never half transformed, because a partly-rewritten command looks migrated and is worse than an untouched one. `migrate` exits non-zero when any command failed.
- **`HideFlags` is marked approximate.** It was a bitmask over several tooltip sections and the modern equivalent hides the whole tooltip, so it is translated but flagged for human review rather than presented as exact.

## feat(migrate): hand verification to the game

`verify` writes every migrated command into `.mcfunction` files — chunked at 200 lines so an error points at a small file, named after the source dimension, each command preceded by a comment naming the coordinates it came from. Load the pack in a 1.21 instance and `/reload`: every syntax error is reported by the authority, and the comment above the line says which command block to go fix.

Python cannot confirm that `minecraft:potion_contents` takes the shape we produced. The game can.

## test(migrate): 62 tests

Every transformation rule with a real command string in and the expected string out, as specified. Plus the SNBT parser's round-trip fidelity, unknown-key preservation, idempotency across all rules, failure handling, the classifier, both inventory formats, the report, and the verification pack.

Runs standalone (`python -m unittest discover -s tests`) or under pytest with the rest of the workspace.
