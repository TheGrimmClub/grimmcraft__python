# grimmcraft-migrate

Migrate Minecraft Java Edition command strings from **1.19** syntax to **1.21**
syntax — for command-block commands extracted out of Anvil region files into an
inventory.

**Standard library only.** This package has no dependencies at all, so it can be
copied out of the workspace and run on a bare Python 3.12. Its CLI is `argparse`
and its tests are `unittest`, for the same reason.

```bash
# 1. look before you leap — what does this corpus actually contain?
python -m grimmcraft_migrate.cli classify commands.json

# 2. rewrite it, with a report of every change
python -m grimmcraft_migrate.cli migrate commands.json -o migrated.json -r report.md

# 3. hand the result to the game's own parser
python -m grimmcraft_migrate.cli verify migrated.json -o verification-pack
```

## What it migrates

| # | Change | Version |
|---|--------|---------|
| 1 | Item NBT → data components (`sword{Enchantments:…}` → `sword[minecraft:enchantments=…]`) | 1.20.5 |
| 2 | Nested item schema (`Count`/`tag` → `count`/`components`) | 1.20.5 |
| 3 | Sign text (`Text1`…`Text4` → `front_text.messages`) | 1.20 |
| 4 | Attribute renames (`generic.movement_speed` → `minecraft:movement_speed`) | 1.20.5 / 1.21.2 |
| 6 | Block positions (`{X:1,Y:2,Z:3}` → `[I;1,2,3]`) | 1.20.5 |

Text components (5) are deliberately **not** rewritten: legacy JSON strings are
still parsed by 1.21, so converting them would change bytes without changing
behaviour.

## Design

**Classify first.** `classify` counts what is there before anything is rewritten,
so effort goes to the rules the corpus actually needs. This is the only pass that
uses regular expressions — a miscount is harmless.

**Parse, don't pattern-match.** The transformation runs on a real SNBT tokenizer
and parser (`snbt.py`), because `{Enchantments:[{id:"…",lvl:5s}]}` nests and
quotes may contain braces. Nodes remember *how* they were written — `5s` keeps
its short suffix, a single-quoted string keeps its quotes — so untouched values
re-serialise byte-for-byte and types are never silently changed.

**Nothing is dropped.** A legacy key with no mapping moves into
`minecraft:custom_data` and is listed in the report, which is what the game
itself does with data it does not recognise.

**Idempotent by construction.** Each pass tests for the *legacy* shape before
acting, so modern input matches nothing and a second run is a no-op. Asserted in
the tests over every rule.

**Fails loudly.** A command whose NBT will not parse is written to the report
with the reason and left **completely unchanged** in the output — never half
transformed, because a partly-rewritten command looks migrated and is worse than
an untouched one. The `migrate` subcommand exits non-zero when any command failed.

## Verification

Python cannot confirm that `minecraft:potion_contents` takes the shape we
produced. The game can. `verify` writes every migrated command into
`.mcfunction` files (chunked at 200 lines, named after their source dimension,
each command preceded by a comment naming the coordinates it came from). Load the
pack in a 1.21 instance and `/reload`: every syntax error is reported by the
authority, pointing at the line — and the comment above it tells you which
command block to go fix.

## Tests

```sh
task migrate:test                        # via pytest, with the rest of the workspace
python -m unittest discover -s tests     # or standalone, no runner needed
```

Every transformation rule has at least one test with a real command string in and
the expected string out, plus idempotency tests across all of them.
