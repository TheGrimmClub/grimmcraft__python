# Changelog — grimmcraft-core

## refactor(core): standardise build on uv_build + srcs

`pyproject.toml` — switched to the `uv_build` backend with `module-root = "srcs"` so the package matches the rest of the workspace and its editable install resolves from `srcs/`.
