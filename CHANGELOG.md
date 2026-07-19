# Changelog for GrimmCraft Python Workspace

> **NOTE:**
> Workspace-level summary. Per-package detail lives in each package's `CHANGELOG.md`.

## refactor(grimmclub): make grimmclub the single access point — 2026-07-19

Settles an architecture question that had never actually been decided: is
`grimmclub` the main API, or does it sit below `grimmclub-filesystem`? Neither —
it had been doing two jobs, which is why the answer was unclear.

    grimmclub                 front door for teachers and trainees
      ├── grimmclub-standardlib   stdlib facade, logging, house vocabulary
      └── grimmclub-filesystem    files, archives, transfers, config, guards

`grimmclub-standardlib` is new, carrying what moved out of `grimmclub`.
`grimmclub` now holds no implementation, only re-exports. `grimmclub-filesystem`
depends on standardlib and drops the second copy of `yes`/`no`/`true`/`false`/
`Any` it had grown — there is now one definition in the workspace, not two that
can drift. Every previous import still resolves.


## feat(filesystem): typed file guards, a Config class, and `task new-filetype` — 2026-07-19

`expect_*` guards for every `FileType`, split into the structural / content /
document layers, with `expect()` dispatching to each. `FileType.matches()`
answers by inspection where possible (an archive by its magic number) and by
suffix only where nothing else can. `Config` becomes a real class with a `with`
block that saves only on a clean exit, and the module stops shipping one
project's configuration defaults — each tool registers its own.
`task new-filetype` writes a new type into all four places it has to appear, or
refuses. See `packages/grimmclub-filesystem/CHANGELOG.md`.


## refactor(examples): collect every example into grimmcraft-examples — 2026-07-19

- [New package](./packages/grimmcraft-examples/CHANGELOG.md)

The 12 example scripts from four packages, plus the `generated/` datapacks they produce, now live in one package. The motivation is dependency honesty: `dungeon_room.py` imported `grimmcraft_decompiler` while sitting in a package that declared no such dependency, and only ran because the workspace venv had everything. Fixed three latent bugs on the way (two Taskfile tasks pointing at files that do not exist, two stale `grimmclub` dependency declarations), and — because examples moved into `srcs/` and are now type-checked — an imprecise `Circuit.place()` signature in grimmcraft-redstone. Task names change: `compiler:tutorial` → `examples:tutorial`. 
## chore(grimmoire): add the teaching materials as a submodule — 2026-07-19

`TheGrimmClub/grimmoire` at `grimmoire/`, excluded from ruff and pytest — it is another repo's content, and its snippets are lesson material that is deliberately imperfect. Clone with `--recurse-submodules`.

## style(lint): take ruff to zero — 2026-07-19

- All packages 

286 errors → 0, split three ways rather than blanket-silenced. Exempted 257 `E501` in grimmcraft-data's *generated* registry modules (a registry row does not fit in 100 columns, and wrapping 1505 of them would be undone by the next regeneration) and the `F403`/`F405` in grimmclub's facade `__init__` (a star re-export is the entire point of that module). Fixed the rest properly — including the 15 `Optional[X]` annotations, which are *emitted by generator templates*, so the generators were fixed too or the next regeneration would have undone it.

## feat(decompiler): implement grimmcraft-decompiler — 2026-07-19

- [Improved package](./packages/grimmcraft-decompiler/CHANGELOG.md)

Datapack → IR → machines → Python, the inverse of the compiler, in three levels that degrade into each other. The reader is self-verifying: each parse is rendered back through the real `Dialect` and accepted only if it reproduces the line byte-for-byte, so a parser cannot silently normalise a pack. `compile(decompile(pack)) == pack` byte-for-byte over every committed example, at both levels, across two versions — which doubles as a regression guard on the forward compiler. 

## feat(monorepo): import filesystem + world from grimmcraft__town — 2026-07-19

- [New package, moved from grimmcraft__town](./packages/grimmclub-filesystem/CHANGELOG.md)
- [New package, moved from grimmcraft__town](./packages/grimmcraft-world/CHANGELOG.md)

`filesystem` → `grimmclub-filesystem` and `minecraft` → `grimmcraft-world`, converted to this repo's conventions (srcs/ layout, uv_build, absolute imports, Taskfiles, mypy --strict). Gained an NBT *writer*, `read_chunk`, and the `expect_*` guards. The town repo still has its copies; removing them needs a PR there. See each package's `CHANGELOG.md`.

## feat(structures): create the grimmcraft-structures package — 2026-07-19

Save and restore Minecraft `.nbt` structures: capture a box of blocks out of a saved world's region files, store it as a template in a datapack, and place it from a machine. 
## feat(npc): create the grimmcraft-npc package — 2026-07-19

- [new package](./packages/grimmcraft-npc/CHANGELOG.md)
- [updated package](./packages/grimmcraft-core/CHANGELOG.md)

Branching NPC dialogue in the shape Ren'Py made familiar. A dialogue *is* a state machine, so it lowers to a `Machine` and inherits validation, compilation, round-trip and decompilation. Two presentation backends from one source: native `dialog` screens on 1.21.6+, clickable `tellraw` below. 

## feat(migrate): create the grimmcraft-migrate package — 2026-07-19

- [new package](./packages/grimmcraft-migrate/CHANGELOG.md)

Migrate command-block commands from 1.19 to 1.21 syntax, with a real SNBT parser, an explicit mapping table, and a verification datapack that hands checking to the game's own parser. Standard-library only, so it also runs standalone. 

## feat(vocabulary): rich text, place and dialog_show — 2026-07-19

- [updated package](./packages/grimmcraft-core/CHANGELOG.md)

`grimmcraft_core.text` models styled, clickable text components; the `Dialect` renders them, honouring the 1.21.5 `clickEvent` → `click_event` rewrite on the same threshold as JSON → SNBT. `place` and `dialog_show` join `CommandName` so structures and dialogue round-trip like any other effect. `if_score` became a context manager. A plain `str` still renders byte-for-byte as before, so no existing pack changed.

## fix(compiler): never pluralize the always-singular resource folders — 2026-07-19

- [updated package](./packages/grimmcraft-world/CHANGELOG.md)
 
`dimension`, `dimension_type`, `worldgen` and `dialog` were being written to pluralized folders the game does not read. Found by round-tripping a third-party datapack through the new decompiler.

## feat(monorepo): scaffold the grimmcraft_* workspace packages — 2026-07-17

- All packages

Created the initial uv-workspace packages using task and `Taskfile.yaml`: `grimmcraft_core`, `grimmcraft_data`, `grimmcraft_control`, `grimmcraft_cli`, and `grimmcraft_compiler`.

## feat(redstone): create the grimmcraft-redstone package — 2026-07-18

- [new package](./packages/grimmcraft-redsone/CHANGELOG.md)

A simulatable redstone component-graph — signal model, four component families, tick-based simulator, diagnostics, tests, examples and docs.

## fix(env): make editable imports survive iCloud sync — 2026-07-17

- All packages

iCloud sets the macOS `UF_HIDDEN` flag on uv's editable `.pth` files, which `site.py` silently skips — breaking every `grimmcraft_*` import. `Taskfile.yml` now clears the flag on sync (`fix-venv`) and disables uv's implicit re-sync.

## refactor(monorepo): standardize packages on srcs/ + uv_build — 2026-07-17

- All packages

Every package now uses the `uv_build` backend with `module-root = "srcs"`; also fixed the cli wheel/script typos and the data Taskfile include, and added the `redstone:` include to the root `Taskfile.yml`.

## chore(pytest): enable importlib import mode — 2026-07-18

- All packages

`pyproject.toml` adds `--import-mode=importlib` so sibling packages can share test-file base names without collisions.

## feat(monorepo): scaffold the grimmclub workspace packages — 2026-07-17

- All packages

Created the initial uv-workspace packages: `grimmclub`.
\n
## refactor(diagnostics): one diagnostics implementation, not three — 2026-07-19

`grimmclub-diagnostics` carries the `Severity`/`Code`/`Diagnostic`/`DiagnosticBag`
machinery that `grimmcraft-compiler` and `grimmcraft-redstone` had grown
separate, near-identical copies of. The compiler, decompiler and redstone keep
their own catalogues (32 codes) and nothing else.

The package is domain-agnostic on purpose — a test asserts it imports nothing
from `grimmcraft` — because the next thing to sit on top of it, `grimmclub-mentor`,
has to explain every producer's codes without knowing what any of them mean.
