# Changelog — grimmclub-mentor

## feat(mentor): turn diagnostics into teaching

A diagnostic says *what* is wrong. A mentor adds *why it happens* and *where to
learn more*, without changing the diagnostic itself.

    error GC1001: block 'minecraft:grass' does not exist in 1.21.11.
        hint: use 'minecraft:short_grass'
        mentor  Minecraft renames blocks and items between versions.
                → Blocks and their ids: python/beginners/06-blocks-and-ids.md

**Generic on purpose.** Nothing here knows what any code means — they are opaque
strings — and a test asserts the package imports nothing from `grimmcraft`. That
is what will make moving it to its own repository a move rather than a rewrite,
and it is why domain packages *extend* the mentor rather than the mentor
reaching into them.

Explanations arrive two ways, neither privileged:

- **registered from code**, for a package's own baseline;
- **discovered as Markdown** with YAML front matter, which is how the teaching
  material contributes — a teacher edits prose, not Python. A later registration
  wins, so lessons can improve on a package's baseline without a release.

Three deliberate behaviours:

- **A missing teaching repository is not an error.** grimmoire is a submodule and
  may not be checked out. The mentor explains what it has; one that refused to
  start would be worse than useless.
- **Prose is skipped, not rejected.** A lessons folder holds ordinary Markdown
  as well as explanations, so files without front matter are ignored quietly.
- **Unresolved lessons are named anyway, and marked.** Mentioning a lesson that
  is not on disk beats silence — but the report says `→ (not found)` rather than
  implying it is there.

`coverage()` reports how much of a bag can be taught (`1/2 explained`), which is
the number worth watching while the explanations are still being written.
