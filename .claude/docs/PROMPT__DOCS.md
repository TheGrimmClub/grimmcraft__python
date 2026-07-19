# Task: set up Zensical as the grimmcraft documentation site
> [ ] TODO: execute PROMPT__DOCS.md

Set up **Zensical** (the modern static-site generator from the Material for
MkDocs team; https://zensical.org) as the single documentation system for the
grimmcraft monorepo, aggregating the docs of every package
(`grimmcraft-data`, `grimmcraft-core`, `grimmcraft-control`,
`grimmcraft-compiler`, `grimmcraft-redstone`) into one site.

If you suggest a task to execute show it as a taskfile like task with a description element (`desc`).


**Zensical is pre-1.0 and evolving fast — pin a version and verify the current
CLI, config schema, and plugin compatibility against the official docs before
finalizing** (Get started: https://zensical.org/docs/get-started/ ; Compatibility:
https://zensical.org/compatibility/ ). Treat the specifics below as a starting
point, not gospel.

## Install & bootstrap

- Add Zensical as a docs dependency with uv (the repo uses uv), e.g. a `docs`
  dependency group: `uv add --group docs zensical` (or `uv pip install zensical`
  in a venv). Pin the version.
- Bootstrap at the **repo root** with `zensical new .` (this scaffolds a
  `.github/` dir, a `docs/` folder with `index.md`, and a `zensical.toml`).
  Review whatever it generates and adapt — don't blindly keep the defaults.

## Configuration choice (state the tradeoff, then pick)

Zensical auto-detects config in this order: `zensical.toml`, `mkdocs.yml`,
`mkdocs.yaml`, and can read `mkdocs.yml` natively, auto-mapping listed MkDocs
plugins to Zensical modules.

- If the API reference needs **mkdocstrings** (Python autodoc), use a
  `mkdocs.yml` so the plugin ecosystem is available — but **first confirm on the
  compatibility page that the plugins you need are supported**; if one isn't yet,
  either fall back to hand-written API pages or note it as a known gap.
- Otherwise prefer the native `zensical.toml`.

Document which you chose and why in the docs' contributing page.

## Site structure & nav

Single aggregated site. Because MkDocs-style tooling expects one `docs_dir`,
decide and document how per-package docs are pulled in (a root `docs/` tree with
a section per package, or a small sync/symlink/gen step, or a monorepo plugin if
supported). Nav should cover:

- **Home / overview** — what grimmcraft is, the package map, the build pipeline
  (data → core → control → compiler → redstone).
- **Getting started** — install, `uv` workflow, run an example.
- **Per-package sections** — surfacing the docs the other prompts produce:
  - data: the registry enums + advanced loaders reference.
  - core: the domain-class model.
  - control: the state-machine concepts + the Mermaid state diagram.
  - compiler: the version/flavor support matrix + the diagnostics (`GCxxxx`)
    code index.
  - redstone: the component reference table + the example-circuit gallery.
- **API reference** — mkdocstrings (if supported) pointed at each package's
  `src/`, else curated pages.
- **Examples** and **Contributing / docs authoring**.

## Features to enable

- Theme: `modern` (default) — or `classic` if you want to match Material for
  MkDocs exactly. State the choice.
- Search, code copy, syntax highlighting.
- **Mermaid diagrams must render** (the control + redstone docs rely on them) —
  configure `pymdownx.superfences` with a mermaid custom fence in
  `markdown_extensions`.
- Useful Python-Markdown extensions: admonitions, `pymdownx.tabbed`,
  `pymdownx.details`, tables, `toc` with permalinks.

## Taskfile & CI

- Add root `Taskfile.yaml` tasks matching existing style:
  `docs:serve` → `uv run zensical serve` (live preview),
  `docs:build` → `uv run zensical build` (outputs to `site/`).
- If `zensical new` created a `.github/` workflow, review it; otherwise add an
  optional GitHub Pages deploy that runs `zensical build` and publishes `site/`.
  Do not enable auto-deploy without the maintainer's confirmation — leave it as a
  reviewable workflow.

## Deliverable checklist

- `uv run zensical build` succeeds with no errors; `uv run zensical serve` serves
  the site with live reload.
- Nav resolves with no broken internal links; Mermaid diagrams render; code
  blocks have copy buttons; search works.
- If API autodoc is enabled, pages generate for all five packages; if a needed
  plugin isn't yet supported by Zensical, that gap is documented, not silently
  broken.
- `site/` is git-ignored; the chosen config file and docs sources are committed.
- Versions pinned; docs authoring workflow documented; style consistent with the
  repo.
```
