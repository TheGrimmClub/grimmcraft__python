# Changelog — grimmcraft-cli

## fix(cli): correct wheel path and console-script entry point

`pyproject.toml` — fixed the `packages = ["srcs/grimmcraftcraft_cli"]` typo (double "craft") and the stale console script `grimm = "grimm_cli.main:main"` → `grimmcraft = "grimmcraft_cli.main:main"`.

## refactor(cli): standardise build on uv_build + srcs

Switched to the `uv_build` backend with `module-root = "srcs"`.
