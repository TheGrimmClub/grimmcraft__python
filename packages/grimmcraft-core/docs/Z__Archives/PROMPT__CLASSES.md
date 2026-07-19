# Task: define the domain classes for the grimmcraft core package
> [x] run PROMPT__CLASSES.md 

Create the core domain model in the core package (e.g.
`packages/grimmcraft-core/src/grimmcraft_core/`). **First inspect the sibling
packages** (`grimmcraft-data`, `grimmcraft-control`, `grimmcraft-redstone`) and
match their conventions exactly: Python version, `dataclass` vs `pydantic`,
typing style, module layout, docstring style, and how they configure lint/type
checks. The examples below use stdlib `dataclasses` + `typing`; switch to the
repo's actual choice if it differs.

These classes model **live game objects** (an entity moves, an inventory
changes), so entities/containers are **mutable**, while pure value objects
(coordinates) are **immutable/frozen**. Reuse the generated enums from
`grimmcraft-data` (`Block`, `Item`, `Entity`, `VillagerProfession`,
`MobEffect`, …) as the *type* fields — never re-declare those constants here.

If you suggest a task to execute show it as a taskfile like task with a description element (`desc`).

## Package layout

```
grimmcraft_core/
    coordinates.py          # Coordinates, BlockPos, Direction
    protocols.py            # Positioned, Container, Interactable (Protocol/ABC)
    entity/
        __init__.py
        core_entity.py      # CoreEntity (base)
        player.py           # Player
        mob.py              # Mob
        npc.py              # Npc
    item/
        __init__.py
        core_item.py        # CoreItem (base)
        book.py             # Book
        chest.py            # Chest
    workstation/
        __init__.py
        core_workstation.py # CoreWorkstation (base)
        crafting_table.py   # CraftingTable
        furnace.py
        brewing_stand.py
        anvil.py
        enchantment_table.py
```

Re-export the public classes from `grimmcraft_core/__init__.py`.

## Shared abstractions (`protocols.py`)

Define small structural interfaces so behavior is shared by composition, not deep
inheritance:

- `Positioned` — has `position: Coordinates`.
- `Container` — holds items: `slots: list[CoreItem | None]`, `capacity: int`,
  `add(item) -> bool`, `remove(slot) -> CoreItem | None`, `is_full`, `__iter__`.
- `Interactable` — `interact(actor: "CoreEntity") -> None`.

Prefer `typing.Protocol` for duck-typed capabilities; use `abc.ABC` only for the
concrete base classes below.

## `coordinates.py`

- `Coordinates` — frozen dataclass, `x: float, y: float, z: float`. Methods:
  `offset(dx, dy, dz) -> Coordinates`, `__add__`/`__sub__` (with another
  Coordinates or a Direction), `distance_to(other) -> float`,
  `manhattan_to(other) -> int`, `to_block_pos() -> BlockPos`. Hashable.
- `BlockPos` — frozen dataclass of `int` x/y/z for block-grid positions;
  `to_coordinates()` (block center or corner — document which), `offset(...)`,
  `neighbors()`.
- `Direction` — enum of the 6 faces (NORTH/SOUTH/EAST/WEST/UP/DOWN) with a
  `.delta -> tuple[int,int,int]` and `.opposite`. Optional: an 8/16-wind yaw
  helper if the project needs facing.

## `scoreboard.py` and `clock.py`
- generate a minecraft clock via a scoreboard that allows to 
  - show the time in a head up display
  - create events that trigger on a specific hour of the day on a specific minute each hour or a time of day (hour and minute) 
  - create an enum that has things like `noon`, `midnight`, `breakfast`, `lunch`, `teatime` and and `dinner` ...
  - events should trigger a message in the text chat and be useable by the control state machine in the `grimmcraft-control` package
 
## `entity/` — CoreEntity and subclasses

`CoreEntity` (mutable, ABC): `entity_type: Entity` (from grimmcraft-data),
`position: Coordinates`, optional `uuid: UUID` (default `uuid4()`), `name:
str | None`, `health: float`, `max_health: float`. Methods: `move_to(pos)`,
`teleport(pos)`, `distance_to(other)`, `is_alive`, `damage(amount)`,
`heal(amount)`. Implements `Positioned`.

- `Player(CoreEntity)` — adds `inventory: Container` (e.g. a 36-slot Inventory),
  `gamemode: Enum(SURVIVAL/CREATIVE/ADVENTURE/SPECTATOR)`, `xp_level: int`,
  optional `hunger`. Default `entity_type = Entity.PLAYER`.
- `Mob(CoreEntity)` — adds `hostile: bool`, optional `drops` hook and an
  `ai_enabled: bool`. Validate that `entity_type` is a mob-category `Entity`.
- `Npc(Mob | CoreEntity)` — adds `profession: VillagerProfession` (from
  grimmcraft-data) and `trades: list[Trade]` / `dialogue`. Decide whether an Npc
  is-a Mob or a sibling and document the choice.

Add a `post_init`/validator that clamps `health` to `[0, max_health]` and (where
sensible) checks the `entity_type` matches the subclass.

## `item/` — CoreItem and subclasses

`CoreItem` (mutable, base): `item_type: Item` (from grimmcraft-data), `count:
int = 1`, `metadata: dict[str, Any]` (or a typed NBT-ish struct). Methods:
`stack_size` (from `Item.stack_size`), `can_stack_with(other)`, `split(n)`.
Guard `count` against `stack_size`.

- `Book(CoreItem)` — `title: str`, `author: str | None`, `pages: list[str]`.
  Default `item_type = Item.WRITABLE_BOOK` / `Item.WRITTEN_BOOK` (pick and note).
- `Chest(CoreItem, Container)` — a placeable container: `slots` of size 27
  (double chest 54), implements `Container` and `Interactable`. Note the dual
  nature (it is both an item and a placed block) and how you represent a placed
  vs carried chest (e.g. an optional `position`).

## `workstation/` — CoreWorkstation and subclasses

`CoreWorkstation` (base, ABC, `Positioned` + `Interactable`): `block_type:
Block` (from grimmcraft-data), `position: Coordinates`. `interact(actor)` opens
the station.

- `CraftingTable(CoreWorkstation)` — a 3×3 grid; `place(item, row, col)`,
  `craft() -> CoreItem | None` (may integrate with `grimmcraft-data`'s recipe
  loader later — leave a clean seam, don't hardcode recipes here).
- Stub the other common stations (`Furnace`, `BrewingStand`, `Anvil`,
  `EnchantingTable`) with `block_type` defaults and `interact` signatures so the
  hierarchy is obvious; full behavior can come later.

## Cross-cutting requirements

- Full type hints; `from __future__ import annotations` if the repo uses it.
- `__repr__`/equality via dataclasses; frozen only for value objects.
- Validation in `__post_init__` (or pydantic validators): non-negative counts,
  health bounds, enum-category checks. Raise `ValueError` with clear messages.
- No circular imports — keep `coordinates.py` and `protocols.py` dependency-free;
  entities/items/workstations import from them, not vice versa.
- Depend on `grimmcraft-data` for all enum types; add it as a package dependency
  if not already present.
- Docstrings on every public class/method explaining intent, not mechanics.

## Deliverable checklist

- Everything imports: `python -c "import grimmcraft_core"`.
- Type-checks clean under the repo's checker (mypy/pyright).
- A short smoke test: build a `Player` at some `Coordinates`, `move_to` a new
  position, put a `Book` in their inventory, place a `Chest`, and `interact`
  with a `CraftingTable` — asserting the obvious post-conditions.
- Style is consistent with the existing grimmcraft packages.
```
