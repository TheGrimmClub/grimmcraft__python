# Changelog — grimmcraft-core

## fix(game): three real bugs, and one enum instead of two — 2026-07-19

`game.py` had a rule enum with one member, spelled wrongly, that nothing used:

- **The spelling was wrong.** `do_daylight_cycle` should be `doDaylightCycle`.
  Verified against Mojang's own data, not memory: of 63 rules, zero contain an
  underscore.
- **The enum was bypassed.** `rule()` and `set_rule()` took `str`, so
  `set_rule("doDayLightCycle", True)` type-checked and created a dead rule. They
  take `GameRule` now, which is what makes the enum worth having.
- **`rule()` raised `KeyError` for anything unset**, so reading a rule on a
  fresh session failed. It returns `None`, or a caller-supplied `default`.

Values are typed `bool | int` — the only two kinds Minecraft has, so a wider
type would let `3.7` through here and fail in game.

Two more found while in there: `ban_player` merely called `remove_player`, so a
ban lasted until the player reconnected; and `set_mode` accepted an unknown
player and silently lost the setting, though `mode()` rejects the same name.

**`GameMode` is gone; `GameModeType` is the one enum.** `player.py` defined a
second, identical copy of the same four values in the same package — the shape
that produced the duplicate `yes`.


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
