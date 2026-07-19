# Changelog — grimmclub-filesystem

## feat(filesystem): import from grimmcraft__town as `grimmclub-filesystem`

Moved out of `TheGrimmClub/grimmcraft__town` (where it was `filesystem`) and renamed to fit this workspace's naming. The single interface to `os`, `pathlib`, `zipfile`, `ftplib` and `urllib`, under `srcs/grimmclub_filesystem/`.

- `core.py` — shared aliases (`SystemPath`, `path_like`) and the `yes`/`no` constants. Deliberately re-exports the standard-library names the sibling modules use, so the package is their only point of contact with it; `__all__` now states that intent to both ruff and mypy.
- `paths.py` — `as_path`, `ensure_dir`, `is_junk` (macOS/editor clutter), `locate_directory` (find a folder by marker file).
- `archive.py` — `Archive` class plus `create_archive` / `extract_archive` / `list_archive`, skipping `__MACOSX` and friends.
- `transfer.py` — `http_download`, `ftp_download`, `download`, and a YAML-describable `fetch`.
- `config.py` — load/save the shared `config.yaml`, with a `.bak` safety net.

## feat(filesystem): guards that fail usefully

`checks.py` — `expect_file`, `expect_dir`, `expect_json`, `expect_json_object`, and `ContentError`.

The check is trivial; the value is the message. These distinguish the four ways a path disappoints you — parent folder missing, file missing (listing siblings with a `difflib` did-you-mean), wrong kind, present-but-empty — and quote the offending line of malformed JSON with its line and column. They raise rather than collect diagnostics, because they guard programmer mistakes at the edges; the compiler's `verify` stays diagnostic-shaped for problems a *user's* pack can have.

## fix(filesystem): extract_archive lost the directory of a Path argument

`extract_archive` and `list_archive` reduced a `SystemPath` argument to its `.name`, so they only worked when the archive happened to sit in the working directory. They now open the full path and use the basename only as the archive's label.

## refactor(filesystem): repo conventions

`srcs/` layout, `uv_build` backend, absolute imports, `py.typed`, a `Taskfile.yml` (`fs:` namespace), and mypy `--strict` clean — return annotations and `dict[str, Any]` type arguments throughout. Its 34 tests pass unchanged.
