# Changelog — grimmclub

## refactor(grimmclub): become the single access point, holding no implementation

The package is now the front door and nothing else: it re-exports
`grimmclub-standardlib` (the standard-library facade, logging helpers and house
vocabulary) and `grimmclub-filesystem` (paths, archives, transfers,
configuration, the `expect_*` guards), and contains no code of its own.

    from grimmclub import Path, dataclass, StrEnum   # the standard library
    from grimmclub import log, banner, yes, no       # teaching helpers
    from grimmclub import archive, paths, expect     # working with files

Every previous import still resolves, so nothing downstream changed.

The reason for the split is that the old package did two jobs at once — front
door *and* shared vocabulary — which point in opposite directions. A working
library such as `grimmcraft-decompiler` needs `expect_file` and archive
handling; it should not thereby acquire a curated re-export of `itertools`.
Trainees are spared the distinction: they import `grimmclub` and get the lot.

`grimmclub.Path` remains the *logging* subclass, while
`grimmclub_filesystem` uses plain `pathlib.Path` as `SystemPath` — a backup tool
that logged every file it copied would be unusable. Both are `pathlib.Path`
instances, so they mix freely; the distinction is now documented in both places.

