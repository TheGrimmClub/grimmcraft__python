# Changelog for GrimmCraft Python Workspace

Workspace-level summary. Per-package detail lives in each package's
`CHANGELOG.md`.

## feat(redstone): create the grimmcraft-redstone package — 2026-07-18

A simulatable redstone component-graph — signal model, four component families,
tick-based simulator, diagnostics, tests, examples and docs. See
`packages/grimmcraft-redstone/CHANGELOG.md`.

## fix(env): make editable imports survive iCloud sync — 2026-07-17

iCloud sets the macOS `UF_HIDDEN` flag on uv's editable `.pth` files, which
`site.py` silently skips — breaking every `grimmcraft_*` import. `Taskfile.yml`
now clears the flag on sync (`fix-venv`) and disables uv's implicit re-sync.

## refactor(monorepo): standardise packages on srcs/ + uv_build — 2026-07-17

Every package now uses the `uv_build` backend with `module-root = "srcs"`; also
fixed the cli wheel/script typos and the data Taskfile include, and added the
`redstone:` include to the root `Taskfile.yml`.

## chore(pytest): enable importlib import mode — 2026-07-18

`pyproject.toml` adds `--import-mode=importlib` so sibling packages can share test-file base names without collisions.

## chore(monorepo): scaffold the grimmcraft_* workspace packages — 2026-07-17

Created the initial uv-workspace packages: `grimmcraft_core`, `grimmcraft_data`,
`grimmcraft_control`, `grimmcraft_cli`, `grimmcraft_compiler` and `grimmclub`.
