# Changelog — grimmcraft-control

## refactor(control): move src/ → srcs/ and standardise on uv_build

Renamed the source folder `src/` → `srcs/` and added `[tool.uv.build-backend] module-root = "srcs"` so the layout and build backend match the rest of the workspace.
