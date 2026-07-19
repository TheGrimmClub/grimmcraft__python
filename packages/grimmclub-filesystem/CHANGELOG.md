# Changelog — grimmclub-filesystem

## feat(paths): cross-platform junk detection, with reasons

`is_junk_directory` knew five names, four of them macOS. It now covers macOS,
Windows and Linux, plus the editors and sync tools that litter a working tree —
discharging the two TODOs on the function.

Several kinds of junk cannot be expressed as fixed names, which the old set
could not represent at all: `._notes.txt` (AppleDouble sidecars) is named after
the file it shadows, `.Trash-1000` after a user id, `~$report.docx` after the
document it locks, `.nfs0000001a` after an inode. Those now match by pattern.

`junk_reason()` returns *why* a path is junk rather than a bare boolean, so a
tool can report "3 files skipped: macOS Finder folder settings" instead of
"3 files skipped". Keeping the reason beside the name also stops the table
becoming a list of magic strings nobody dares delete.

`is_junk_path` is the accurate name — the check applies to files as much as
folders (`.DS_Store` and `Thumbs.db` are files) and is called on zip members.
`is_junk_directory` remains as an alias, since callers already use it.

Fixed while testing: the check used `as_path`, which expands `~`. A file
genuinely named `~$report.docx` — precisely the Office lock file we want to
catch — was therefore treated as a home-directory reference and raised. Junk
detection reads a name; it has no business resolving a path.

`.git`, `.gitignore` and `.github` are deliberately *not* junk: dropping version
control from an archive loses history. The "must not be junk" test list is the
one that matters most, since a false positive silently discards someone's data.


## feat(checks): a guard per FileType, and `task new-filetype`

`checks.py` is now split into the layers its guards actually fall into — layer
one structural (`expect_directory`, `expect_file`, `expect_link`), layer two
content (`expect_text`, `expect_markdown`, `expect_script`, `expect_yaml`,
`expect_binary`, `expect_archive`, `expect_executable`), layer three structured
documents (`expect_json`, `expect_json_object`, `expect_yaml_document`,
`expect_yaml_mapping`) — and `expect()` dispatches to each rather than falling
through to the generic guard, so the error names the kind that was wanted.

All of them raise and return the path rather than returning `bool`. Two
functions sharing the `expect_` prefix but not its contract would be a trap; the
plain predicate already exists as `FileType.ARCHIVE.matches(path)`, which is
where the real test lives — the guards only add the message.

`FileType.matches()` answers by inspection where that is possible and by suffix
only where it is not: an archive is an archive because its magic number says so,
a `.md` file is Markdown because it is called that. Text is decided by
decodability *and* the absence of a NUL byte, since plenty of binary formats
decode as UTF-8 by accident.

A file type lives in four places, and forgetting one fails differently each
time — a missing suffix entry silently matches nothing, a missing dispatch arm
quietly falls back to the generic guard. `task new-filetype -- YAML --value 102
--layer text --suffixes .yaml,.yml` writes all four, refuses rather than
half-applies, and parses the result before saving:

    error: value 250 is outside the text band (100-199); the bands are what
           is_text/is_binary read, so a value in the wrong one lies

## feat(config): registerable defaults, a Config class, and a `with` block

Three TODOs discharged.

**The defaults were one project's.** `DEFAULT_CONFIG` hard-coded sections for
`guard`, `scout`, `blacksmith` and `town` — four applications that live in a
different repository. A filesystem library cannot know what a configuration
should contain, so it no longer claims to: it ships none, and each tool calls
`register_defaults("guard", {...})` at import. `default_config()` returns a
fresh copy, because the previous module-level constant could be mutated in
place by accident.

**`Config` is now the interface.** It owns path, data, load, save, restore and
backup_path, with `path` and `data` as properties — assigning a new path drops
the stale contents rather than serving the previous file's data. Reading is
lazy, so constructing one touches no disk. The module functions remain as thin
wrappers for callers that want a single operation.

**A `with` block does make sense here**, and it is implemented: `__enter__`
loads, `__exit__` saves — but only on a clean exit. A body that raised may have
left the configuration half-edited, and writing that is worse than losing it.
`__exit__` returns `None` rather than `False`, since a `bool` return type tells
a type checker the block might swallow the exception.

The same question was asked of the `expect_` guards and answered **no** — the
reasoning is recorded in `checks.py` in place of the TODO. A context manager
wants an acquire and a release; those functions inspect a path and either return
it or raise, so a `with` would add a scope with no meaning at its edges.

## feat(checks): YAML validation, not just a suffix check

`expect_yaml` checks the name, which is all a name can tell you.
`expect_yaml_document` and `expect_yaml_mapping` mirror the JSON pair: they
parse with `safe_load` — configuration is data and must never construct Python
objects — and report the offending line, so a file *called* `.yaml` that is not
YAML fails there rather than three frames away.

## test(core): cover StringChecker and the standard-library re-exports

Discharges the `TODO: create tests` on the class. The tests also pin a
surprising consequence: `special_chars` contains `.`, so cleaning a name strips
its extension (`backup.zip` → `backupzip`). That is now documented on the class
rather than discovered — and is why `Archive` is built with `do_cleanup=no`
wherever a real file name matters.


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
- `paths.py` — `as_path`, `create_full_path`, `is_junk_directory` (macOS/editor clutter), `locate_directory` (find a folder by marker file).
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
