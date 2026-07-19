"""Auto-generated from PrismarineJS/minecraft-data.
Minecraft Java Edition 1.21.11 — 40 effect types.

Each member's .value is the integer registry id for this version;
.string_id is the namespaced id (e.g. 'minecraft:speed').
.display_name is the human label.
.type is 'good' or 'bad'.
NOTE: numeric ids are stable within a version but change between
versions (Java has no permanent numeric ids since 1.13).
Do not edit by hand; regenerate with _generate/effects.py."""

from grimmclub_standardlib import Enum


class Effect(Enum):
    def __new__(cls, num_id, string_id, display_name, type):
        obj = object.__new__(cls)
        obj._value_ = num_id
        obj.string_id = string_id
        obj.display_name = display_name
        obj.type = type
        return obj

    SPEED = (0, "minecraft:speed", "Speed", "good")
    SLOWNESS = (1, "minecraft:slowness", "Slowness", "bad")
    HASTE = (2, "minecraft:haste", "Haste", "good")
    MINING_FATIGUE = (3, "minecraft:mining_fatigue", "Mining Fatigue", "bad")
    STRENGTH = (4, "minecraft:strength", "Strength", "good")
    INSTANT_HEALTH = (5, "minecraft:instant_health", "Instant Health", "good")
    INSTANT_DAMAGE = (6, "minecraft:instant_damage", "Instant Damage", "bad")
    JUMP_BOOST = (7, "minecraft:jump_boost", "Jump Boost", "good")
    NAUSEA = (8, "minecraft:nausea", "Nausea", "bad")
    REGENERATION = (9, "minecraft:regeneration", "Regeneration", "good")
    RESISTANCE = (10, "minecraft:resistance", "Resistance", "good")
    FIRE_RESISTANCE = (11, "minecraft:fire_resistance", "Fire Resistance", "good")
    WATER_BREATHING = (12, "minecraft:water_breathing", "Water Breathing", "good")
    INVISIBILITY = (13, "minecraft:invisibility", "Invisibility", "good")
    BLINDNESS = (14, "minecraft:blindness", "Blindness", "bad")
    NIGHT_VISION = (15, "minecraft:night_vision", "Night Vision", "good")
    HUNGER = (16, "minecraft:hunger", "Hunger", "bad")
    WEAKNESS = (17, "minecraft:weakness", "Weakness", "bad")
    POISON = (18, "minecraft:poison", "Poison", "bad")
    WITHER = (19, "minecraft:wither", "Wither", "bad")
    HEALTH_BOOST = (20, "minecraft:health_boost", "Health Boost", "good")
    ABSORPTION = (21, "minecraft:absorption", "Absorption", "good")
    SATURATION = (22, "minecraft:saturation", "Saturation", "good")
    GLOWING = (23, "minecraft:glowing", "Glowing", "bad")
    LEVITATION = (24, "minecraft:levitation", "Levitation", "bad")
    LUCK = (25, "minecraft:luck", "Luck", "good")
    BAD_LUCK = (26, "minecraft:bad_luck", "Bad Luck", "bad")
    SLOW_FALLING = (27, "minecraft:slow_falling", "Slow Falling", "good")
    CONDUIT_POWER = (28, "minecraft:conduit_power", "Conduit Power", "good")
    DOLPHINS_GRACE = (29, "minecraft:dolphins_grace", "Dolphin's Grace", "good")
    BAD_OMEN = (30, "minecraft:bad_omen", "Bad Omen", "bad")
    HERO_OF_THE_VILLAGE = (31, "minecraft:hero_of_the_village", "Hero of the Village", "good")
    DARKNESS = (32, "minecraft:darkness", "Darkness", "bad")
    TRIAL_OMEN = (33, "minecraft:trial_omen", "Trial Omen", "bad")
    RAID_OMEN = (34, "minecraft:raid_omen", "Raid Omen", "bad")
    WIND_CHARGED = (35, "minecraft:wind_charged", "Wind Charged", "bad")
    WEAVING = (36, "minecraft:weaving", "Weaving", "bad")
    OOZING = (37, "minecraft:oozing", "Oozing", "bad")
    INFESTED = (38, "minecraft:infested", "Infested", "bad")
    BREATH_OF_THE_NAUTILUS = (39, "minecraft:breath_of_the_nautilus", "Breath of the Nautilus", "good")
