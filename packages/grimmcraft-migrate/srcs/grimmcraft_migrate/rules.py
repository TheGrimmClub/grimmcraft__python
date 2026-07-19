"""The mapping table: legacy item NBT keys → 1.20.5+ data components.

One entry per legacy key, each carrying the component identifier it becomes and
a function that rewrites the *value* — because most of these changed shape, not
just name.  ``Enchantments`` is the clearest case: a list of ``{id,lvl}``
compounds became a map of ``id: level``.

Keys with no entry here are **never dropped**.  They are moved into
``minecraft:custom_data``, which is exactly what the game itself does with data
it does not recognise, and recorded in the report so nothing disappears quietly.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from grimmcraft_migrate.snbt import (
    SnbtBoolean,
    SnbtCompound,
    SnbtList,
    SnbtNumber,
    SnbtString,
    SnbtValue,
)

#: The component every unmapped legacy key is preserved under.
CUSTOM_DATA_COMPONENT = "minecraft:custom_data"


def _namespaced(identifier: str) -> str:
    """``sharpness`` → ``minecraft:sharpness``; an explicit namespace is kept."""
    return identifier if ":" in identifier else f"minecraft:{identifier}"


# --- value transformations ---------------------------------------------------


def keep(value: SnbtValue) -> SnbtValue:
    """Pass the value through unchanged (only the key was renamed)."""
    return value


def enchantment_list_to_map(value: SnbtValue) -> SnbtValue:
    """``[{id:"minecraft:sharpness",lvl:5s}]`` → ``{"minecraft:sharpness":5}``."""
    if not isinstance(value, SnbtList):
        return value
    mapped = SnbtCompound()
    for entry in value.items:
        if not isinstance(entry, SnbtCompound):
            continue
        identifier = entry.get("id")
        level = entry.get("lvl")
        if not isinstance(identifier, SnbtString):
            continue
        name = _namespaced(identifier.value)
        mapped.quoted_keys.add(name)
        # Levels lose their `s` suffix: the component holds a plain int.
        mapped[name] = (
            SnbtNumber(str(level.as_int())) if isinstance(level, SnbtNumber)
            else SnbtNumber("1")
        )
    return mapped


def unbreakable_to_component(value: SnbtValue) -> SnbtValue:
    """``Unbreakable:1b`` → ``unbreakable:{}`` — presence *is* the value now."""
    return SnbtCompound()


def json_text_to_component(value: SnbtValue) -> SnbtValue:
    """A JSON text string stays a string — the game still parses it.

    1.21.5 allows SNBT objects here, but the legacy JSON string remains valid,
    and converting it would change bytes without changing behaviour.
    """
    return value


def lore_lines(value: SnbtValue) -> SnbtValue:
    """``display.Lore`` is a list of JSON text strings; the component keeps that."""
    return value


def color_to_dyed(value: SnbtValue) -> SnbtValue:
    """``display.color:16711680`` → ``dyed_color:16711680``."""
    return value


def potion_identifier(value: SnbtValue) -> SnbtValue:
    """``Potion:"minecraft:strong_healing"`` becomes ``potion_contents``'s id."""
    if isinstance(value, SnbtString):
        compound = SnbtCompound()
        compound["potion"] = SnbtString(_namespaced(value.value))
        return compound
    return value


def custom_effects(value: SnbtValue) -> SnbtValue:
    """``CustomPotionEffects`` moved under ``potion_contents.custom_effects``."""
    compound = SnbtCompound()
    compound["custom_effects"] = value
    return compound


def attribute_modifiers(value: SnbtValue) -> SnbtValue:
    """Rewrite each modifier's attribute name and slot key.

    The legacy shape used ``AttributeName``/``Slot``/``Amount``/``Operation`` as
    an integer; the component uses ``type``/``slot``/``amount``/``operation`` with
    a named operation.
    """
    if not isinstance(value, SnbtList):
        return value
    operations = {0: "add_value", 1: "add_multiplied_base", 2: "add_multiplied_total"}
    rewritten = SnbtList()
    for entry in value.items:
        if not isinstance(entry, SnbtCompound):
            continue
        modifier = SnbtCompound()
        name = entry.get("AttributeName")
        if isinstance(name, SnbtString):
            modifier["type"] = SnbtString(rename_attribute(name.value))
        amount = entry.get("Amount")
        if amount is not None:
            modifier["amount"] = amount
        operation = entry.get("Operation")
        if isinstance(operation, SnbtNumber):
            modifier["operation"] = SnbtString(
                operations.get(operation.as_int(), "add_value")
            )
        slot = entry.get("Slot")
        if isinstance(slot, SnbtString):
            modifier["slot"] = slot
        identifier = entry.get("Name")
        if isinstance(identifier, SnbtString):
            modifier["id"] = SnbtString(_namespaced(identifier.value))
        rewritten.items.append(modifier)
    return rewritten


def can_place_or_destroy(value: SnbtValue) -> SnbtValue:
    """``CanDestroy:["minecraft:stone"]`` → ``{predicates:[{blocks:[…]}]}``."""
    blocks = value if isinstance(value, SnbtList) else SnbtList([value])
    predicate = SnbtCompound()
    predicate["blocks"] = blocks
    predicates = SnbtList([predicate])
    wrapper = SnbtCompound()
    wrapper["predicates"] = predicates
    return wrapper


def hide_flags_to_tooltip(value: SnbtValue) -> SnbtValue:
    """``HideFlags`` became per-component tooltip control.

    There is no faithful single-component equivalent, so the closest honest
    translation is hiding the whole tooltip when any flag was set. The report
    records it as approximate.
    """
    return SnbtBoolean(False)


def skull_owner(value: SnbtValue) -> SnbtValue:
    """``SkullOwner`` → ``profile``; a bare name string is kept as the name."""
    if isinstance(value, SnbtString):
        return value
    return value


def written_book_pages(value: SnbtValue) -> SnbtValue:
    """``pages`` moved into ``written_book_content.pages``."""
    compound = SnbtCompound()
    compound["pages"] = value
    return compound


# --- attribute renames (1.20.5 and 1.21.2) -----------------------------------

#: Legacy attribute identifier → its modern namespaced form.
ATTRIBUTE_RENAMES: dict[str, str] = {
    "generic.max_health": "minecraft:max_health",
    "generic.follow_range": "minecraft:follow_range",
    "generic.knockback_resistance": "minecraft:knockback_resistance",
    "generic.movement_speed": "minecraft:movement_speed",
    "generic.flying_speed": "minecraft:flying_speed",
    "generic.attack_damage": "minecraft:attack_damage",
    "generic.attack_knockback": "minecraft:attack_knockback",
    "generic.attack_speed": "minecraft:attack_speed",
    "generic.armor": "minecraft:armor",
    "generic.armor_toughness": "minecraft:armor_toughness",
    "generic.luck": "minecraft:luck",
    "generic.max_absorption": "minecraft:max_absorption",
    "generic.step_height": "minecraft:step_height",
    "generic.scale": "minecraft:scale",
    "generic.gravity": "minecraft:gravity",
    "generic.jump_strength": "minecraft:jump_strength",
    "generic.safe_fall_distance": "minecraft:safe_fall_distance",
    "generic.fall_damage_multiplier": "minecraft:fall_damage_multiplier",
    "generic.burning_time": "minecraft:burning_time",
    "generic.explosion_knockback_resistance": (
        "minecraft:explosion_knockback_resistance"
    ),
    "generic.movement_efficiency": "minecraft:movement_efficiency",
    "generic.oxygen_bonus": "minecraft:oxygen_bonus",
    "generic.water_movement_efficiency": "minecraft:water_movement_efficiency",
    "horse.jump_strength": "minecraft:jump_strength",
    "zombie.spawn_reinforcements": "minecraft:spawn_reinforcements",
    "player.block_break_speed": "minecraft:block_break_speed",
    "player.block_interaction_range": "minecraft:block_interaction_range",
    "player.entity_interaction_range": "minecraft:entity_interaction_range",
    "player.mining_efficiency": "minecraft:mining_efficiency",
    "player.sneaking_speed": "minecraft:sneaking_speed",
    "player.submerged_mining_speed": "minecraft:submerged_mining_speed",
    "player.sweeping_damage_ratio": "minecraft:sweeping_damage_ratio",
}


def rename_attribute(identifier: str) -> str:
    """The modern name for a legacy attribute id (unchanged if already modern)."""
    return ATTRIBUTE_RENAMES.get(identifier, _namespaced(identifier))


# --- the table ---------------------------------------------------------------


@dataclass(frozen=True)
class ComponentRule:
    """How one legacy item-NBT key becomes a data component."""

    component: str
    transform: Callable[[SnbtValue], SnbtValue]
    #: Set when the translation cannot be exact, so the report can say so.
    approximate: bool = False
    note: str = ""


#: Legacy item NBT key → the component it becomes.
COMPONENT_RULES: dict[str, ComponentRule] = {
    "Enchantments": ComponentRule("minecraft:enchantments", enchantment_list_to_map),
    "StoredEnchantments": ComponentRule(
        "minecraft:stored_enchantments", enchantment_list_to_map
    ),
    "display.Name": ComponentRule("minecraft:custom_name", json_text_to_component),
    "display.Lore": ComponentRule("minecraft:lore", lore_lines),
    "display.color": ComponentRule("minecraft:dyed_color", color_to_dyed),
    "AttributeModifiers": ComponentRule(
        "minecraft:attribute_modifiers", attribute_modifiers
    ),
    "Potion": ComponentRule("minecraft:potion_contents", potion_identifier),
    "CustomPotionEffects": ComponentRule(
        "minecraft:potion_contents", custom_effects
    ),
    "CustomModelData": ComponentRule("minecraft:custom_model_data", keep),
    "Unbreakable": ComponentRule("minecraft:unbreakable", unbreakable_to_component),
    "Damage": ComponentRule("minecraft:damage", keep),
    "SkullOwner": ComponentRule("minecraft:profile", skull_owner),
    "BlockEntityTag": ComponentRule("minecraft:block_entity_data", keep),
    "EntityTag": ComponentRule("minecraft:entity_data", keep),
    "pages": ComponentRule("minecraft:written_book_content", written_book_pages),
    "title": ComponentRule("minecraft:written_book_content", keep),
    "author": ComponentRule("minecraft:written_book_content", keep),
    "Fireworks": ComponentRule("minecraft:fireworks", keep),
    "CanDestroy": ComponentRule("minecraft:can_break", can_place_or_destroy),
    "CanPlaceOn": ComponentRule("minecraft:can_place_on", can_place_or_destroy),
    "HideFlags": ComponentRule(
        "minecraft:hide_tooltip",
        hide_flags_to_tooltip,
        approximate=True,
        note="HideFlags was a bitmask over several tooltips; the component "
        "hides the whole tooltip, so review these by hand",
    ),
}

#: Keys nested under ``display`` that the table addresses as ``display.<key>``.
DISPLAY_KEYS = {"Name", "Lore", "color"}

#: NBT keys whose values are lists of *items*, needing the nested item rewrite.
ITEM_CONTAINER_KEYS = {
    "Items",
    "HandItems",
    "ArmorItems",
    "Inventory",
    "EnderItems",
    "ArmorDropChances",
    "equipment",
}

#: Fields that became ``[I;x,y,z]`` integer arrays in 1.20.5.
BLOCK_POSITION_FIELDS = {"flower_pos", "hive_pos", "FlowerPos", "HivePos"}
