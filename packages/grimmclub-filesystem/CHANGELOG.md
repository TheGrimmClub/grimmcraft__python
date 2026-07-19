# Changelog — grimmclub-filesystem

## refactor(archive): name and path as properties, real name validation

`Archive` now knows *where* it lives, not only what it is called.

- **`Archive(name, path=None)`** takes the folder as a second argument. With one
  set, `exists()`, `list()` and `extract()` work without being handed a path
  every time; without one, the archive is simply a name, which is all
  `create_archive` needs.
- **`name`, `path` and `full_path` are properties.** Assigning to `name` cleans
  it exactly as the constructor does, so cleaning cannot be bypassed after
  construction; assigning to `path` coerces a `str` to a `SystemPath`, so every
  reader gets the same type. `full_path` is *derived* from the two rather than
  stored, so the three can never disagree.
- **`FORBIDDEN_CHARACTERS` is now the real set** — everything Windows forbids
  (`< > : " / \ | ? *` and the control characters) plus the POSIX separators —
  and `RESERVED_NAMES` covers `CON`, `PRN`, `AUX`, `NUL`, `COM1-9`, `LPT1-9`,
  which Windows refuses whatever the extension.
- **`is_valid_name()` was inverted.** It looped over the forbidden characters
  but tested `name.count(' ') == 0`, so it ignored the character it was
  checking and declared every name *without* a space invalid. It now checks
  what it says it checks, and `do_needs_date` is implemented rather than
  `pass`.
- **`is_valid_archive()` is complete.** It was a syntax error — a missing colon
  on the `def` line, which meant the whole package failed to import — and had
  no `return`. It now verifies existence, name validity, and that the file is a
  readable zip whose CRCs check out, because existence alone is not enough: a
  truncated download exists.
- **`append_date()` keeps the extension last.** `backup.zip` became
  `backup.zip__20260719`, which is no longer recognisably a zip; it is now
  `backup__20260719.zip`.
- **`extract()`'s `do_overwrite` is implemented**, having previously been
  accepted and ignored — every extraction overwrote regardless.

22 tests added, covering the properties, every forbidden-character class,
reserved names, the date stamp, overwrite behaviour, and `is_valid_archive`
against a file that exists but is not a zip. The class's `TODO: create tests`
is discharged.


## feat(filesystem): import from grimmcraft__town as `grimmclub-filesystem`

Moved out of `TheGrimmClub/grimmcraft__town` (where it was `filesystem`) and renamed to fit this workspace's naming. The single interface to `os`, `pathlib`, `zipfile`, `ftplib` and `urllib`, under `srcs/grimmclub_filesystem/`.

- `core.py` — shared aliases (`SystemPath`, `path_like`) and the `yes`/`no` constants. Deliberately re-exports the standard-library names the sibling modules use, so the package is their only point of contact with it; `__all__` now states that intent to both ruff and mypy.
- `paths.py` — `as_path`, `ensure_dir`, `is_junk` (macOS/editor clutter), `locate_directory` (find a folder by marker file).
- `archive.py` — `Archive` class plus `create_archive` / `extract_archive` / `list_archive`, skipping `__MACOSX` and friends.
- `transfer.py` — `http_download`, `ftp_download`, `download`, and a YAML-describable `fetch`.
- `config.py` — load/save the shared `config.yaml`, with a `.bak` safety net.

## feat(filesystem): guards that fail usefully

`checks.py` — `expect_file`, `expect_directory`, `expect_json`, `expect_json_object`, and `ContentError`.

The check is trivial; the value is the message. These distinguish the four ways a path disappoints you — parent folder missing, file missing (listing siblings with a `difflib` did-you-mean), wrong kind, present-but-empty — and quote the offending line of malformed JSON with its line and column. They raise rather than collect diagnostics, because they guard programmer mistakes at the edges; the compiler's `verify` stays diagnostic-shaped for problems a *user's* pack can have.

## fix(filesystem): extract_archive lost the directory of a Path argument

`extract_archive` and `list_archive` reduced a `SystemPath` argument to its `.name`, so they only worked when the archive happened to sit in the working directory. They now open the full path and use the basename only as the archive's label.

## refactor(filesystem): repo conventions

`srcs/` layout, `uv_build` backend, absolute imports, `py.typed`, a `Taskfile.yml` (`fs:` namespace), and mypy `--strict` clean — return annotations and `dict[str, Any]` type arguments throughout. Its 34 tests pass unchanged.
