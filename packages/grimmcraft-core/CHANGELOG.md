# Changelog — grimmcraft-core

## feat(core): rich text components

`text.py` — `Text` and `ClickEvent`, modelling Minecraft's text component: colour, the five styles, click actions (`run_command`, `suggest_command`, `open_url`, `copy_to_clipboard`, `change_page`, `show_dialog`) and a hover tooltip, with children that inherit style.

Pure data: rendering it to the version-correct syntax is the `Dialect`'s job, as with every other command. A bare `str` remains valid everywhere a component is accepted, and an unstyled `Text` renders exactly as one — so nothing existing changes.

## feat(core): the dialogue model

`entity/dialogue.py` — `Dialogue`, `Scene`, `Option`, `Condition`. Branching NPC dialogue as Ren'Py models it: named scenes that say lines, run effects, and then offer a menu, jump onwards, or end.

The data model only — pure, immutable, and free of Minecraft syntax. The builder and the lowering to a `Machine` live in `grimmcraft-npc`, because both need command constructors from `grimmcraft-control`, which depends on this package. `problems()` and `unreachable()` report structural faults as sentences, so a caller can surface them as diagnostics rather than an exception.

## feat(core): the `CommandLike` protocol

`protocols.py` gains `CommandLike` — structurally `grimmcraft_control.machine.Command`, but stated as a protocol so core's domain types can hold commands without importing `grimmcraft-control`, which depends on core and would make the two circular.

Its members are read-only properties rather than plain attributes, because `Command` is a *frozen* dataclass: a settable `name: str` could not be satisfied by any immutable type.

---

## refactor(core): standardise build on uv_build + srcs

`pyproject.toml` — switched to the `uv_build` backend with `module-root = "srcs"` so the package matches the rest of the workspace and its editable install resolves from `srcs/`.
