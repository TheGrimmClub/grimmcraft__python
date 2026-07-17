# grimmcraft — Python monorepo

A [uv workspace](https://docs.astral.sh/uv/concepts/workspaces/) of Python
packages, orchestrated with [Task](https://taskfile.dev). All packages share a
single lockfile (`uv.lock`) and virtualenv (`.venv`), and can depend on each
other locally.

## Layout

```
.
├── Taskfile.yml              # root orchestrator (workspace-wide tasks)
├── pyproject.toml            # workspace root + shared dev tooling / tool config
├── uv.lock                   # single lockfile for the whole workspace
└── packages/
    ├── grimmcraft-core/           # library
    │   ├── pyproject.toml
    │   ├── src/grimm_core/
    │   ├── tests/
    │   └── Taskfile.yml       # per-package tasks (core: namespace)
    └── grimmcraft-cli/            # app that depends on grimmcraft-core
        ├── pyproject.toml     #   → [tool.uv.sources] grimmcraft-core = { workspace = true }
        ├── src/grimm_cli/
        ├── tests/
        └── Taskfile.yml       # per-package tasks (cli: namespace)
```

## Prerequisites

- [`uv`](https://docs.astral.sh/uv/) (manages Python + dependencies)
- [`task`](https://taskfile.dev/installation/)

## Quick start

```bash
task install     # sync the whole workspace into .venv
task check       # lint + typecheck + test (what CI should run)
task cli:run -- Grimm   # → Hello, Grimm!
```

## Tasks

Run `task --list` to see everything. Workspace-wide tasks auto-discover
packages under `packages/*`:

| Task              | What it does                                     |
| ----------------- | ------------------------------------------------ |
| `install`         | `uv sync --all-packages`                         |
| `test`            | run every package's tests                        |
| `lint`            | `ruff check` the workspace                       |
| `format`          | `ruff format` + autofix                          |
| `typecheck`       | `mypy` every package                             |
| `build`           | `uv build --all-packages` → `dist/`              |
| `check`           | lint + typecheck + test                          |
| `clean`           | remove build artifacts and caches                |
| `new-package -- <name>` | scaffold a new workspace package           |

Per-package tasks are namespaced by the `includes:` block in the root
`Taskfile.yml` — e.g. `task core:test`, `task cli:build`, `task cli:run -- Alice`.

## Adding a package

```bash
task new-package -- grimmcraft-data
```

Then add an `includes:` entry in the root `Taskfile.yml` to expose its
per-package tasks. The workspace-wide tasks (`test`, `build`, …) pick it up
automatically. To depend on another workspace package, add it to the new
package's `dependencies` and declare the source:

```toml
[tool.uv.sources]
grimmcraft-core = { workspace = true }
```
