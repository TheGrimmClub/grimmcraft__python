"""grimmcraft_data — vanilla Minecraft (Java Edition) data as typed Python.

Everything here is generated from authoritative sources by the scripts in
``_generate/`` (PrismarineJS/minecraft-data for the enums and richer datasets;
Mojang's ``reports/registries.json`` for the exhaustive registries).

Two flavors of data are exposed:

* **Enums** — one member per registry entry, ``.value`` is the integer id::

      from grimmcraft_data import Block, Item
      Block.OAK_LOG.value            # -> int registry id
      Item(893)                      # -> reverse lookup

* **Richer datasets** — frozen dataclasses backed by lazily-loaded bundled JSON,
  with ids resolved back to the enums where natural::

      from grimmcraft_data import recipes_for, block_loot, collision_boxes, translate
      recipes_for(Item.CHEST)        # -> list[Recipe]
      block_loot(Block.STONE)        # -> LootTable
      collision_boxes(Block.STONE)   # -> list[AABB]
      translate("block.minecraft.stone")

Exhaustive registry enums (``sound_event``, ``menu``, ``mob_effect``, …) are
produced by ``_generate/advanced_registry.py`` from a local Mojang report and are
imported on demand once generated; they are intentionally not re-exported here.
"""

from __future__ import annotations

# --- Richer datasets: dataclasses + accessors --------------------------------
from . import attribute, collision_shape, language, loot, recipe
from .attribute import ATTRIBUTES, Attribute

# --- Core enums (one member per registry entry) ------------------------------
from .biome import Biome
from .block import Block
from .collision_shape import AABB, collision_boxes
from .effect import Effect
from .enchantment import Enchantment
from .entity import Entity
from .food import Food
from .instrument import Instrument
from .item import Item
from .language import all_keys, translate
from .loot import Drop, LootTable, block_loot, entity_loot
from .particle import Particle
from .recipe import Recipe, all_recipes, recipes_for

__all__ = [
    # enums
    "Biome",
    "Block",
    "Effect",
    "Enchantment",
    "Entity",
    "Food",
    "Instrument",
    "Item",
    "Particle",
    # dataset modules (for `grimmcraft_data.recipe`, etc.)
    "attribute",
    "collision_shape",
    "language",
    "loot",
    "recipe",
    # recipe
    "Recipe",
    "recipes_for",
    "all_recipes",
    # loot
    "Drop",
    "LootTable",
    "block_loot",
    "entity_loot",
    # collision
    "AABB",
    "collision_boxes",
    # attribute (call it as `attribute.attribute(resource)`)
    "Attribute",
    "ATTRIBUTES",
    # language
    "translate",
    "all_keys",
]
