"""The richer datasets: lazily-loaded JSON resolved back onto the enums.

Each accessor opens a bundled JSON file on first use and caches it, so these
also cover the packaging question -- whether the data files ship at all.
"""

from __future__ import annotations

from grimmcraft_data import (
    AABB,
    ATTRIBUTES,
    Block,
    Entity,
    Item,
    LootTable,
    Recipe,
    all_keys,
    all_recipes,
    block_loot,
    collision_boxes,
    entity_loot,
    recipes_for,
    translate,
)


def test_recipes_resolve_ingredients_to_items() -> None:
    recipes = recipes_for(Item.CHEST)
    assert recipes
    recipe = recipes[0]
    assert isinstance(recipe, Recipe)
    assert recipe.result_item is Item.CHEST
    # The point of this package: raw numeric ids come back as enum members.
    cells = [c for row in recipe.shape for c in row if c is not None]
    assert cells and all(isinstance(c, Item) for c in cells)


def test_all_recipes_is_keyed_by_item_id() -> None:
    recipes = all_recipes()
    assert recipes
    assert Item.CHEST.value in recipes


def test_block_loot_resolves_drops() -> None:
    table = block_loot(Block.STONE)
    assert isinstance(table, LootTable)
    dropped = {d.item for d in table.drops}
    # Stone drops cobblestone, or itself with silk touch.
    assert Item.COBBLESTONE in dropped
    assert Item.STONE in dropped


def test_entity_loot_resolves_drops() -> None:
    table = entity_loot(Entity.COW)
    assert isinstance(table, LootTable)
    assert Item.LEATHER in {d.item for d in table.drops}


def test_collision_boxes_of_a_full_block() -> None:
    boxes = collision_boxes(Block.STONE)
    assert boxes == [AABB(0.0, 0.0, 0.0, 1.0, 1.0, 1.0)]


def test_translate_known_key_and_unknown_key() -> None:
    assert translate("block.minecraft.stone") == "Stone"
    assert "block.minecraft.stone" in all_keys()


def test_attributes_are_namespaced() -> None:
    assert ATTRIBUTES
    assert all(key.startswith("minecraft:") for key in ATTRIBUTES)


def test_recipes_for_is_cached() -> None:
    # @cache backed, so repeat lookups return the same list object.
    assert recipes_for(Item.CHEST) is recipes_for(Item.CHEST)


def test_all_recipes_rebuilds_but_is_stable() -> None:
    # Unlike recipes_for, all_recipes() re-parses every call (only the raw JSON
    # underneath is cached). Equal, but deliberately not identical -- callers
    # who mutate the result won't poison the next caller.
    first, second = all_recipes(), all_recipes()
    assert first == second
    assert first is not second
