"""Auto-generated from PrismarineJS/minecraft-data.
Minecraft Java Edition 1.21.11 — 43 enchantment types.

Each member's .value is the integer registry id for this version;
.string_id is the namespaced id (e.g. 'minecraft:sharpness').
.display_name is the human label.
.max_level is the highest level.
.category is the applicable item group.
NOTE: numeric ids are stable within a version but change between
versions (Java has no permanent numeric ids since 1.13).
Do not edit by hand; regenerate with _generate/enchantments.py."""

from __future__ import annotations

from grimmclub_standardlib import Enum


class Enchantment(Enum):
    string_id: str
    display_name: str
    max_level: int
    category: str

    def __new__(cls, num_id: int, string_id: str, display_name: str, max_level: int, category: str) -> Enchantment:
        obj = object.__new__(cls)
        obj._value_ = num_id
        obj.string_id = string_id
        obj.display_name = display_name
        obj.max_level = max_level
        obj.category = category
        return obj

    AQUA_AFFINITY = (0, "minecraft:aqua_affinity", "Aqua Affinity", 1, "head_armor")
    BANE_OF_ARTHROPODS = (1, "minecraft:bane_of_arthropods", "Bane of Arthropods", 5, "weapon")
    BINDING_CURSE = (2, "minecraft:binding_curse", "Curse of Binding", 1, "equippable")
    BLAST_PROTECTION = (3, "minecraft:blast_protection", "Blast Protection", 4, "armor")
    BREACH = (4, "minecraft:breach", "Breach", 4, "mace")
    CHANNELING = (5, "minecraft:channeling", "Channeling", 1, "trident")
    DENSITY = (6, "minecraft:density", "Density", 5, "mace")
    DEPTH_STRIDER = (7, "minecraft:depth_strider", "Depth Strider", 3, "foot_armor")
    EFFICIENCY = (8, "minecraft:efficiency", "Efficiency", 5, "mining")
    FEATHER_FALLING = (9, "minecraft:feather_falling", "Feather Falling", 4, "foot_armor")
    FIRE_ASPECT = (10, "minecraft:fire_aspect", "Fire Aspect", 2, "fire_aspect")
    FIRE_PROTECTION = (11, "minecraft:fire_protection", "Fire Protection", 4, "armor")
    FLAME = (12, "minecraft:flame", "Flame", 1, "bow")
    FORTUNE = (13, "minecraft:fortune", "Fortune", 3, "mining_loot")
    FROST_WALKER = (14, "minecraft:frost_walker", "Frost Walker", 2, "foot_armor")
    IMPALING = (15, "minecraft:impaling", "Impaling", 5, "trident")
    INFINITY = (16, "minecraft:infinity", "Infinity", 1, "bow")
    KNOCKBACK = (17, "minecraft:knockback", "Knockback", 2, "melee_weapon")
    LOOTING = (18, "minecraft:looting", "Looting", 3, "melee_weapon")
    LOYALTY = (19, "minecraft:loyalty", "Loyalty", 3, "trident")
    LUCK_OF_THE_SEA = (20, "minecraft:luck_of_the_sea", "Luck of the Sea", 3, "fishing")
    LUNGE = (21, "minecraft:lunge", "Lunge", 3, "lunge")
    LURE = (22, "minecraft:lure", "Lure", 3, "fishing")
    MENDING = (23, "minecraft:mending", "Mending", 1, "durability")
    MULTISHOT = (24, "minecraft:multishot", "Multishot", 1, "crossbow")
    PIERCING = (25, "minecraft:piercing", "Piercing", 4, "crossbow")
    POWER = (26, "minecraft:power", "Power", 5, "bow")
    PROJECTILE_PROTECTION = (27, "minecraft:projectile_protection", "Projectile Protection", 4, "armor")
    PROTECTION = (28, "minecraft:protection", "Protection", 4, "armor")
    PUNCH = (29, "minecraft:punch", "Punch", 2, "bow")
    QUICK_CHARGE = (30, "minecraft:quick_charge", "Quick Charge", 3, "crossbow")
    RESPIRATION = (31, "minecraft:respiration", "Respiration", 3, "head_armor")
    RIPTIDE = (32, "minecraft:riptide", "Riptide", 3, "trident")
    SHARPNESS = (33, "minecraft:sharpness", "Sharpness", 5, "sharp_weapon")
    SILK_TOUCH = (34, "minecraft:silk_touch", "Silk Touch", 1, "mining_loot")
    SMITE = (35, "minecraft:smite", "Smite", 5, "weapon")
    SOUL_SPEED = (36, "minecraft:soul_speed", "Soul Speed", 3, "foot_armor")
    SWEEPING_EDGE = (37, "minecraft:sweeping_edge", "Sweeping Edge", 3, "sweeping")
    SWIFT_SNEAK = (38, "minecraft:swift_sneak", "Swift Sneak", 3, "leg_armor")
    THORNS = (39, "minecraft:thorns", "Thorns", 3, "armor")
    UNBREAKING = (40, "minecraft:unbreaking", "Unbreaking", 3, "durability")
    VANISHING_CURSE = (41, "minecraft:vanishing_curse", "Curse of Vanishing", 1, "vanishing")
    WIND_BURST = (42, "minecraft:wind_burst", "Wind Burst", 3, "mace")
