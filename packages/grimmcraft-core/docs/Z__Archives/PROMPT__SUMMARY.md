Key design decisions (per the prompt's "decide and document")

- Conventions matched: stdlib dataclasses + typing + from __future__ import annotations, module-root="srcs" — no pydantic (there's none in the repo). Value objects are frozen=True, slots=True; live objects (entities/items/workstations) are mutable kw_only dataclasses.
- Enums reused from grimmcraft-data: Entity, Item, Block. Mob-category validation reads Entity.type (e.g. hostile/passive).
- NPC is-a Mob (villagers are passive mobs) — documented in the module.
- VillagerProfession defined locally in npc.py with a clear swap-in seam: it's a Mojang registry enum grimmcraft-data doesn't ship yet (needs the server report we don't have).
- GameMode lives in player.py — the repo's game.py has its own broken GameModeType, so I didn't couple to it.
- BlockPos.to_coordinates() = the block's min corner (exact inverse of to_block_pos), documented.
- CraftingTable.craft() is a clean seam — returns None unless a recipe_resolver is injected; no recipes hardcoded (wire grimmcraft_data.recipe later).
- Clock ↔ control seam: advance() returns fired ClockFires and runs per-event callbacks; it never imports grimmcraft-control, so the state machine drives from the return value or a callback.

Two things to flag

1. TODO: game.py is pre-existing broken (not py errors and an actualself-in-default-argument NameError that crashes import grimmcraft_core.game. It's unrelated WIP
(game/gamerules) so I left it untouchedecheck red for core. Want me to fix orremove it?
2. TODO:  grimmcraft_data has 81 pre-existing enum dynamic-attrs + the Part A advancedmodules from the earlier task). They surface when checking core because mypy follows the import. I can tighten the generators to emit strict-cf you want the whole workspace green.
