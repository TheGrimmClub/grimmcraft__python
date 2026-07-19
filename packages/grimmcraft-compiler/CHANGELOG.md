# Changelog — grimmcraft-compiler

## fix(compiler): never pluralise the always-singular resource folders

`category_dir()` pluralised any category not in its table, so a `dimension` resource was written to `data/<ns>/dimensions/` on a pre-1.21 target — a folder Minecraft does not read, silently dropping the dimension.

The 1.21 rename turned `functions` into `function`, but the world-generation registries (`dimension`, `dimension_type`, `worldgen`) arrived in 1.16 *already* singular and were untouched by it, so they now map to themselves. `dialog` joins them from the other direction: it is newer than the rename entirely (1.21.6).

Found by round-tripping a third-party datapack through `grimmcraft-decompiler` — the regression-guard role the round-trip is meant to play for this package.

## feat(compiler): render rich text components

`Dialect.text_component()` accepts a `grimmcraft_core.text.Text` as well as a `str`, with `rich_text()` and `text_document()` for the styled form, and an SNBT serialiser.

Two version splits land on the same 1.21.5 threshold the Dialect already had: JSON → SNBT, and `clickEvent`/`hoverEvent` → `click_event`/`hover_event` with action-specific fields (`command`, `url`) replacing the single `value`.

A plain `str` — or an unstyled `Text` — renders byte-for-byte as before. That equivalence is what lets rich text be added without disturbing a single existing pack; the committed example packs still round-trip identically.

## feat(compiler): render `place` and `dialog_show`

`_r_place` (`place template <id> <pos> [rotation [mirror]]`, 1.19+) and `_r_dialog_show` (`dialog show <targets> <dialog>`, 1.21.6+). The trailing arguments of `place template` are positional, so a mirror without a rotation gets the neutral `none` inserted.

## feat(compiler): `compile_machines(resources=…)`

Extra JSON documents to ship in the pack — the `dialog` screens a dialogue compiles to, for instance. Lowering never produces resources; they come from domain layers built on top of it.

## chore(compiler): regenerate the committed example datapacks

The checked-in packs had drifted from current output: every `INSTALL.md` predated the `format_label` change, chessboard's `INSTALL.md` claimed 1.21.11 while its own `pack.mcmeta` said format 48, and one `.mcfunction` had drifted outright. Regenerated with the examples' own scripts, which is what makes the decompiler's round-trip tests meaningful over these fixtures.
