"""Auto-generated from PrismarineJS/minecraft-data loot tables.

Minecraft Java Edition 1.21.11 — 925 block and 81 entity loot tables.
Bundled source assets: data/1.21.11/blockLoot.json, data/1.21.11/entityLoot.json (loaded lazily).

`Drop.item` is the `Item` enum member for the dropped item (or its bare string
id if that member is absent); `.drop_chance` is the base chance and
`.stack_min`/`.stack_max` the stack-size range.  `block_loot()` / `entity_loot()`
are keyed by bare string id (e.g. "stone", "zombie") and also accept enum
members.
Do not edit by hand; regenerate with _generate/advanced_loot.py."""

from __future__ import annotations

from grimmclub_standardlib import (
    TYPE_CHECKING,
    Any,
    SystemPath,
    TextIO,
    dataclass,
    files,
    json,
    lru_cache,
)

if TYPE_CHECKING:
    from .block import Block
    from .entity import Entity

_BLOCK_DATA = "data/1.21.11/blockLoot.json"
_ENTITY_DATA = "data/1.21.11/entityLoot.json"
_HERE = SystemPath(__file__).parent

try:
    from .item import Item
except Exception:  # pragma: no cover - Item enum optional
    Item = None


@dataclass(frozen=True, slots=True)
class Drop:
    """A single possible drop within a loot table."""

    item: object                  # Item member, or bare string id
    drop_chance: float | None
    stack_min: int | None
    stack_max: int | None
    silk_touch: bool | None
    no_silk_touch: bool | None
    player_kill: bool | None
    block_age: int | None


@dataclass(frozen=True, slots=True)
class LootTable:
    """The set of drops for one source block or entity."""

    source: str                   # bare string id
    drops: tuple[Drop, ...]


def _name(x: object) -> str:
    """Normalize an Item/enum member or id string to a bare (un-namespaced) name."""
    s = getattr(x, "string_id", x)
    return str(s).split(":", 1)[-1]


@lru_cache(maxsize=1)
def _item_by_name() -> dict[str,str]:
    if Item is None:
        return {}
    return {m.string_id.split(":", 1)[-1]: m for m in Item}


def _resolve_item(name: str) -> str:
    return _item_by_name().get(name, name)


def _open(rel: str) -> TextIO:
    try:
        return files(__package__).joinpath(rel).open("r", encoding="utf-8")
    except (ModuleNotFoundError, TypeError, FileNotFoundError):
        return (_HERE / rel).open("r", encoding="utf-8")


def _parse_drop(d: dict[str, Any]) -> Drop:
    rng = d.get("stackSizeRange") or [None, None]
    lo = rng[0] if len(rng) > 0 else None
    hi = rng[1] if len(rng) > 1 else lo
    return Drop(
        item=_resolve_item(d.get("item")),
        drop_chance=d.get("dropChance"),
        stack_min=lo,
        stack_max=hi,
        silk_touch=d.get("silkTouch"),
        no_silk_touch=d.get("noSilkTouch"),
        player_kill=d.get("playerKill"),
        block_age=d.get("blockAge"),
    )


@lru_cache(maxsize=1)
def _tables(rel: str, source_field: str) -> dict[str, LootTable]:
    with _open(rel) as fh:
        rows: list[dict[str, Any]] = json.load(fh)
    out: dict[str, LootTable] = {}
    for row in rows:
        src: str = row[source_field]
        out[src] = LootTable(src, tuple(_parse_drop(d) for d in row.get("drops", [])))
    return out


def block_loot(block: Block | str) -> LootTable | None:
    """Loot table for a block (an `Item`/`Block` member or bare/namespaced id)."""
    return _tables(_BLOCK_DATA, "block").get(_name(block))


def entity_loot(entity: Entity | str) -> LootTable | None:
    """Loot table for an entity (an `Entity` member or bare/namespaced id)."""
    return _tables(_ENTITY_DATA, "entity").get(_name(entity))
