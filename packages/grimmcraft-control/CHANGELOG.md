# Changelog — grimmcraft-control

## feat(control): `if_score` as a context manager

A run of effects sharing one guard now writes its condition once instead of per line:

    with state.cycle.if_score("stage", "tree", 1) as guarded:
        guarded.fill(a, b, Block.OAK_LOG)
        guarded.fill(c, d, Block.OAK_LEAVES)

Same name as the chained form — one concept, not two. The block is grouping only: each effect is still guarded individually, since `mcfunction` has no block syntax to nest them in, and a test asserts both forms produce identical commands.

The `add_transition` with-block already existed but was never exercised anywhere; it now has tests too.

## feat(control): `place` and `dialog_show` join the command vocabulary

`CommandName.PLACE` (`place template`, 1.19+) and `CommandName.DIALOG_SHOW` (`dialog show`, 1.21.6+), with `effects.place()` / `effects.dialog_show()` and matching `EffectWriter` methods.

Keeping these in the *shared* vocabulary, rather than private to the packages that use them, means a placed structure or an opened dialog validates, renders, round-trips and decompiles like any other effect instead of being an opaque `raw` line.

## feat(control): `tellraw` accepts a rich text component

`tellraw` takes a `grimmcraft_core.text.Text` as well as a `str`, for coloured, styled or clickable messages.

---

## refactor(control): move src/ → srcs/ and standardise on uv_build

Renamed the source folder `src/` → `srcs/` and added `[tool.uv.build-backend] module-root = "srcs"` so the layout and build backend match the rest of the workspace.
