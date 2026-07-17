"""Auto-generated from PrismarineJS/minecraft-data `attributes.json`.

Minecraft Java Edition 1.21.11 — 35 entity attributes.

`ATTRIBUTES` is keyed by resource name; each value is a frozen `Attribute`
with its default and clamped min/max.  NOTE: resource names and ranges are
stable within a version but may change between versions.
Do not edit by hand; regenerate with _generate/advanced_attribute.py."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True, slots=True)
class Attribute:
    """A single entity attribute and its allowed value range."""

    name: str
    resource: str
    default: Optional[float]
    min: Optional[float]
    max: Optional[float]


ATTRIBUTES: dict[str, Attribute] = {
    "minecraft:armor": Attribute("armor", "minecraft:armor", 0.0, 0.0, 30.0),
    "minecraft:armor_toughness": Attribute("armorToughness", "minecraft:armor_toughness", 0.0, 0.0, 20.0),
    "minecraft:attack_damage": Attribute("attackDamage", "minecraft:attack_damage", 2.0, 0.0, 2048.0),
    "minecraft:attack_knockback": Attribute("attackKnockback", "minecraft:attack_knockback", 0.0, 0.0, 5.0),
    "minecraft:attack_speed": Attribute("attackSpeed", "minecraft:attack_speed", 4.0, 0.0, 1024.0),
    "minecraft:block_break_speed": Attribute("blockBreakSpeed", "minecraft:block_break_speed", 1.0, 0.0, 1024.0),
    "minecraft:block_interaction_range": Attribute("blockInteractionRange", "minecraft:block_interaction_range", 4.5, 0.0, 64.0),
    "minecraft:burning_time": Attribute("burningTime", "minecraft:burning_time", 1.0, 0.0, 1024.0),
    "minecraft:camera_distance": Attribute("cameraDistance", "minecraft:camera_distance", 4.0, 0.0, 32.0),
    "minecraft:explosion_knockback_resistance": Attribute("explosionKnockbackResistance", "minecraft:explosion_knockback_resistance", 0.0, 0.0, 1.0),
    "minecraft:entity_interaction_range": Attribute("entityInteractionRange", "minecraft:entity_interaction_range", 3.0, 0.0, 64.0),
    "minecraft:fall_damage_multiplier": Attribute("fallDamageMultiplier", "minecraft:fall_damage_multiplier", 1.0, 0.0, 100.0),
    "minecraft:flying_speed": Attribute("flyingSpeed", "minecraft:flying_speed", 0.4, 0.0, 1024.0),
    "minecraft:follow_range": Attribute("followRange", "minecraft:follow_range", 32.0, 0.0, 2048.0),
    "minecraft:gravity": Attribute("gravity", "minecraft:gravity", 0.08, -1.0, 1.0),
    "minecraft:jump_strength": Attribute("jumpStrength", "minecraft:jump_strength", 0.41999998688697815, 0.0, 32.0),
    "minecraft:knockback_resistance": Attribute("knockbackResistance", "minecraft:knockback_resistance", 0.0, 0.0, 1.0),
    "minecraft:luck": Attribute("luck", "minecraft:luck", 0.0, -1024.0, 1024.0),
    "minecraft:max_absorption": Attribute("maxAbsorption", "minecraft:max_absorption", 0.0, 0.0, 2048.0),
    "minecraft:max_health": Attribute("maxHealth", "minecraft:max_health", 20.0, 1.0, 1024.0),
    "minecraft:mining_efficiency": Attribute("miningEfficiency", "minecraft:mining_efficiency", 0.0, 0.0, 1024.0),
    "minecraft:movement_efficiency": Attribute("movementEfficiency", "minecraft:movement_efficiency", 0.0, 0.0, 1.0),
    "minecraft:movement_speed": Attribute("movementSpeed", "minecraft:movement_speed", 0.7, 0.0, 1024.0),
    "minecraft:oxygen_bonus": Attribute("oxygenBonus", "minecraft:oxygen_bonus", 0.0, 0.0, 1024.0),
    "minecraft:safe_fall_distance": Attribute("safeFallDistance", "minecraft:safe_fall_distance", 3.0, -1024.0, 1024.0),
    "minecraft:scale": Attribute("scale", "minecraft:scale", 1.0, 0.0625, 16.0),
    "minecraft:sneaking_speed": Attribute("sneakingSpeed", "minecraft:sneaking_speed", 0.3, 0.0, 1.0),
    "minecraft:spawn_reinforcements": Attribute("spawnReinforcements", "minecraft:spawn_reinforcements", 0.0, 0.0, 1.0),
    "minecraft:step_height": Attribute("stepHeight", "minecraft:step_height", 0.6, 0.0, 10.0),
    "minecraft:submerged_mining_speed": Attribute("submergedMiningSpeed", "minecraft:submerged_mining_speed", 0.2, 0.0, 20.0),
    "minecraft:sweeping_damage_ratio": Attribute("sweepingDamageRatio", "minecraft:sweeping_damage_ratio", 0.0, 0.0, 1.0),
    "minecraft:tempt_range": Attribute("temptRange", "minecraft:tempt_range", 10.0, 0.0, 2048.0),
    "minecraft:water_movement_efficiency": Attribute("waterMovementEfficiency", "minecraft:water_movement_efficiency", 0.0, 0.0, 1.0),
    "minecraft:waypoint_transmit_range": Attribute("waypointTransmitRange", "minecraft:waypoint_transmit_range", 0.0, 0.0, 60000000.0),
    "minecraft:waypoint_receive_range": Attribute("waypointReceiveRange", "minecraft:waypoint_receive_range", 0.0, 0.0, 60000000.0),
}


def attribute(resource: str) -> Optional[Attribute]:
    """Look up an attribute by its resource name."""
    return ATTRIBUTES.get(resource)
