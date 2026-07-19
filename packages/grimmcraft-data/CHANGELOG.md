# Changelog — grimmcraft-data

## feat(villager): profession and job-site registries — 2026-07-19

`VillagerProfession` (15 members) and `VillagerWorkstation` (13), with lookups
both ways, and the stopgap enum in `grimmcraft-core` deleted in favour of them.

The profession list is generated from the shipped `language.json`. The
profession-to-block mapping could not be: Mojang publishes it only in Java
source, so it is curated — and checked against `language.json` and the `Block`
enum at generation time, under `--check`, and in the tests. A new profession or
a mistyped block fails loudly rather than shipping a hole.

`point_of_interest` is deliberately absent — POI types have no translation keys
to generate from, and hand-writing a registry is what the plan ruled out.


## fix(tasks): correct the root Taskfile include for this package

The root `Taskfile.yml` referenced `Taskfile.yml`, but this package's tasks live in `Taskfile.yaml`; the include was pointed at the correct file so `data:` tasks load. No changes to the package sources themselves (it already used `uv_build` with `module-root = "srcs"`).
