# Task: generate the villager profession and workstation registries
> [ ] TODO: execute PROMPT__VILLAGER_REGISTRIES.md

Add `villager_profession` and `point_of_interest` to `grimmcraft-data`, generated
like every other registry rather than hand-written, and delete the stopgap enum
that `grimmcraft-core` currently carries.

## Why this is outstanding

`grimmcraft-core/entity/npc.py` defines `VillagerProfession` locally and says so:

> `VillagerProfession` is defined locally as a stopgap: it is a Mojang *registry*
> enum that `grimmcraft-data` does not yet ship (it requires the server data
> report). When `grimmcraft_data.villager_profession` is generated, swap this
> import to reuse it and delete the local enum.

Nothing maps a profession to the block that creates it — `farmer` ↔ `composter`,
`librarian` ↔ `lectern`, `toolsmith` ↔ `smithing_table`. A villager NPC needs
exactly that mapping, and neither package has it.

**A villager workstation is not a subset of the workstations already modelled.**
`grimmcraft-core/workstation/` covers `ANVIL`, `CRAFTING_TABLE`,
`ENCHANTING_TABLE`, `FURNACE` and `BREWING_STAND` — *player* utility blocks.
Only `brewing_stand` is also a villager job site. The twelve blocks that make a
villager take a profession are absent entirely:

| Profession | Job site block | Profession | Job site block |
|---|---|---|---|
| `armorer` | `blast_furnace` | `librarian` | `lectern` |
| `butcher` | `smoker` | `mason` | `stonecutter` |
| `cartographer` | `cartography_table` | `shepherd` | `loom` |
| `cleric` | `brewing_stand` | `toolsmith` | `smithing_table` |
| `farmer` | `composter` | `weaponsmith` | `grindstone` |
| `fisherman` | `barrel` | `nitwit` | *(none)* |
| `fletcher` | `fletching_table` | `none` | *(none)* |
| `leatherworker` | `cauldron` | | |

So this needs its own registry — `villager_workstation` — rather than being
inferred from what `grimmcraft-core` happens to model, or buried inside
`point_of_interest`. The two ideas share blocks but answer different questions:
*"what can a player use here?"* versus *"what job does this give a villager?"*

## Why it needs a different pipeline

Every other registry here comes from PrismarineJS/minecraft-data, which does not
publish professions or points of interest. These come from Mojang's own **server
data report**:

```sh
java -DbundlerMainClass=net.minecraft.data.Main -jar server.jar --reports
# → generated/reports/registries.json   (all registry ids, incl. villager_profession
#                                        and point_of_interest_type)
```

`data:generate-registry-enums` already accepts a `REGISTRIES=/path/to/registries.json`
override, so the hook exists — what is missing is the profession/POI generator
and the step that produces the report.

**Note the version scheme.** The latest Minecraft is now **26.2** (calendar
versioning; see `packages/grimmcraft-decompiler/docs/support-matrix.md`), and
this workspace's support table still stops at 1.21.11. Decide which version the
registries are generated for before running anything — regenerating against a
newer game than the compiler supports would put ids in the data that no target
can emit.

## What to generate

**`villager_profession.py`** — one enum member per profession, carrying its
namespaced id, and the workstation block that creates it:

```python
class VillagerProfession(Enum):
    FARMER = ("minecraft:farmer", "minecraft:composter")
    LIBRARIAN = ("minecraft:librarian", "minecraft:lectern")
    ...
    @property
    def string_id(self) -> str: ...
    @property
    def workstation(self) -> str | None: ...   # NONE and NITWIT have none
```

`string_id` matters: it is the accessor `grimmcraft-compiler`'s validation and
`dialect.id_string()` already rely on for every other data enum. Match it.

**`villager_workstation.py`** — the job-site blocks, as their own enum, with the
profession each one creates:

```python
class VillagerWorkstation(Enum):
    COMPOSTER = ("minecraft:composter", "minecraft:farmer")
    LECTERN = ("minecraft:lectern", "minecraft:librarian")
    ...
    @property
    def string_id(self) -> str: ...
    @property
    def profession(self) -> str: ...
```

Its own module, not a table inside `villager_profession.py`, because the
question runs both ways: a villager NPC asks "which block do I need?", and a
world scanner asks "what will this block turn a villager into?". Neither is the
derived direction.

**`point_of_interest.py`** — the POI types and the blocks that provide them.
Every job site is a POI, but so are beds, bells and the nether portal, so this
is the wider registry rather than a synonym for the one above. Generate it from
the same report; it is what makes the workstation mapping verifiable rather than
hand-copied.

Two POIs matter as much as the job sites and must not be treated as trimmings:

- **`home` — the bed.** Beds decide village population and breeding. A village
  with workstations and no beds has no villagers in it for long.
- **`meeting` — the bell.** The midday gathering point.

**There is no hearth or fireplace POI.** A campfire is not a point of interest
and villagers ignore it; the bell is the gathering point. If a village layout
wants a hearth it is a `grimmcraft-structures` decoration, not a registry entry —
do not add one here and do not let a generated file imply one exists.

**Accessors**, in the style of `loot.py` / `recipe.py`:

```python
def profession_for_workstation(block) -> VillagerProfession | None
def workstation_for_profession(profession) -> Block | None
```

## Follow-through

- Delete the stopgap enum in `grimmcraft-core/entity/npc.py` and import from
  `grimmcraft_data`, removing the docstring note that describes it as temporary.
  `Npc.profession` keeps its type; only its source changes.
- `grimmcraft-core/workstation/` models *player* workstations and should keep
  doing so — but `core_workstation.py` can then say which of them is also a job
  site, and the twelve missing job-site blocks become answerable: model them
  only where they have behaviour worth modelling, and let the data carry the
  rest. Do not widen `CoreWorkstation` to mean both things.
- `grimmcraft-npc` (Taterzens presets) writes `Professions` entries with a
  `ProfessionType` id — feed it from this enum rather than a string literal.

## Out of scope: containers that move

A related gap, deliberately *not* part of this task, recorded so it is not
mistaken for one. Chests exist on entities as well as blocks, and the registry
already names them:

```
OAK_CHEST_BOAT … PALE_OAK_CHEST_BOAT, BAMBOO_CHEST_RAFT   (11 hulls)
CHEST_MINECART
DONKEY, MULE, LLAMA, TRADER_LLAMA                          (ChestedHorse)
```

Camels carry **no** chest — no inventory at all. Easy to assume otherwise, since
they are the ride introduced after donkeys.

This is not a point of interest and not a block, so it belongs to
`grimmcraft-core` and `grimmcraft-structures`, not here. It matters because
`item/chest.py` satisfies `Container` but also carries `place(position)` and
`is_placed`, which assume a *block* position. A structure file stores blocks and
entities as separate lists, so a capture that only walks blocks loses a chest
boat and everything in it, silently. Fix that where capture lives, not by
widening a registry.

## Tests

- `string_id` round-trips for every member, and matches the `Block`/`Item`
  convention — the compiler's validation depends on it.
- The workstation mapping is complete and symmetric: every profession with a
  workstation resolves back to itself through
  `profession_for_workstation(workstation_for_profession(p))`, and every
  `VillagerWorkstation` resolves back through the reverse.
- The two enums agree: the set of professions naming a workstation equals the
  set of professions named by a workstation. A mapping that disagrees with
  itself is the bug this pair of tests exists to catch.
- `NONE` and `NITWIT` have **no** workstation, and the accessors return `None`
  rather than raising — they are real professions with no block.
- Every workstation block id exists in `Block` for the generated version. A
  mapping that names a block the registry does not have is the failure mode
  worth catching, since it only shows up in game.
- The generator is deterministic: running it twice produces identical output.
  The existing generated modules are checked in, so drift shows up as a diff.

## Taskfile

Add to `packages/grimmcraft-data/Taskfile.yaml`, beside the existing generators:

```yaml
  generate-villager-data:
    desc: Generate the villager profession + point-of-interest registries from a
          Mojang server data report (override the path with REGISTRIES=...)
    cmds:
      - uv run python srcs/grimmcraft_data/_generate/advanced_villager.py
```

Note the generators are themselves linted and type-checked, while their *output*
is exempt from `E501` (see the root `pyproject.toml`) — so write the generator to
the usual standard and let the emitted rows be as long as they need to be.
Whatever it emits must use `X | None` rather than `Optional[X]`: the other
generators were fixed for that and this one should not reintroduce it.
