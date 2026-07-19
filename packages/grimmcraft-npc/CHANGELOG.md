# Changelog — grimmcraft-npc

## feat(npc): branching dialogue in the shape Ren'Py made familiar

New package (depends on `grimmcraft-core`, `grimmcraft-control`, `grimmcraft-compiler`), under `srcs/grimmcraft_npc/`.

A dialogue is named **scenes** that say lines, run effects, and then either offer a **menu**, jump onwards, or end. That is a Ren'Py `label` with its `say` statements and `menu` block — and it is also, exactly, a state machine:

| Ren'Py | grimmcraft |
|---|---|
| `label start:` | a state |
| `e "line"` | the state's enter effects |
| `menu:` choice | a transition, event `choice_<n>` |
| `jump other` | the transition's target |
| `if flag:` | a `when_score` condition |

So a dialogue lowers to a `Machine` and inherits the whole existing pipeline — validation, compilation, the round-trip guarantee, and decompilation back to readable Python. No new runtime.

- `builder.py` — `new_dialogue()`, `SceneDraft`, `MenuDraft`, `OptionDraft`. Mirrors `MachineBuilder`'s `with`-block grouping; effects go through the same `EffectWriter` every state and transition uses.
- `lower.py` — `lower_dialogue()`, producing a `Machine` plus any JSON resources.

The data model lives in `grimmcraft-core` (`entity/dialogue.py`) as pure immutable data with no Minecraft syntax; the builder and lowering live here, because both need command constructors from `grimmcraft-control` — which depends on core, so core cannot depend on it.

## feat(npc): two presentation backends, one source

Only how a scene is *shown* depends on the target:

- **1.21.6+** — a vanilla `dialog` screen. Each scene becomes a `data/<ns>/dialog/<dialogue>/<scene>.json` resource, shown with `dialog show @s`. A menu is a `minecraft:multi_action` whose buttons carry `run_command`; a `goto` scene is a `minecraft:notice` with a Continue button; an ending scene omits `action` and gets the default OK button.
- **earlier** — clickable chat. Lines become `tellraw`, and each option a `tellraw` whose `clickEvent` runs the dispatcher function.

A test asserts both backends produce **identical** states, transitions and guards; only presentation may differ. The dialog JSON follows the schema as documented (`multi_action` with `actions`, `run_command` without a leading slash).

Scene effects run *before* the scene is shown, so an item handed over is in hand before the player reads about it.

### Known limitation
Vanilla dialogs cannot conditionally *hide* a button, so a guarded option renders but does nothing when its condition fails.

## test(npc): 20 tests

The model (declaration order, dangling `goto`, a scene with no ending or two endings, unreachable scenes), the lowering (scenes → states, options → transitions, guards → conditions, effect ordering, final states), both backends, and the agreement between them.

## Still to come
The Taterzens NPC body — skin, behaviour, equipment, and movement waypoints (`TaterzenNPCTag.PathTargets`) — that speaks these lines. Dialogue itself is pure vanilla and needs no mod.
