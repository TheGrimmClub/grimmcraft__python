"""Auto-generated from PrismarineJS/minecraft-data.
Minecraft Java Edition 1.21.11 — 40 effect types.

Each member's .value is the integer registry id for this version;
.string_id is the namespaced id (e.g. 'minecraft:speed').
.display_name is the human label.
.type is 'good' or 'bad'.
NOTE: numeric ids are stable within a version but change between
versions (Java has no permanent numeric ids since 1.13).
Do not edit by hand; regenerate with _generate/effects.py."""

from enum import Enum


class Effect(Enum):
    def __new__(cls, num_id, string_id, display_name, type):
        obj = object.__new__(cls)
        obj._value_ = num_id
        obj.string_id = string_id
        obj.display_name = display_name
        obj.type = type
        return obj

    SPEED = (0, "minecraft:Speed", "Speed", "good")
    SLOWNESS = (1, "minecraft:Slowness", "Slowness", "bad")
    HASTE = (2, "minecraft:Haste", "Haste", "good")
    MININGFATIGUE = (3, "minecraft:MiningFatigue", "Mining Fatigue", "bad")
    STRENGTH = (4, "minecraft:Strength", "Strength", "good")
    INSTANTHEALTH = (5, "minecraft:InstantHealth", "Instant Health", "good")
    INSTANTDAMAGE = (6, "minecraft:InstantDamage", "Instant Damage", "bad")
    JUMPBOOST = (7, "minecraft:JumpBoost", "Jump Boost", "good")
    NAUSEA = (8, "minecraft:Nausea", "Nausea", "bad")
    REGENERATION = (9, "minecraft:Regeneration", "Regeneration", "good")
    RESISTANCE = (10, "minecraft:Resistance", "Resistance", "good")
    FIRERESISTANCE = (11, "minecraft:FireResistance", "Fire Resistance", "good")
    WATERBREATHING = (12, "minecraft:WaterBreathing", "Water Breathing", "good")
    INVISIBILITY = (13, "minecraft:Invisibility", "Invisibility", "good")
    BLINDNESS = (14, "minecraft:Blindness", "Blindness", "bad")
    NIGHTVISION = (15, "minecraft:NightVision", "Night Vision", "good")
    HUNGER = (16, "minecraft:Hunger", "Hunger", "bad")
    WEAKNESS = (17, "minecraft:Weakness", "Weakness", "bad")
    POISON = (18, "minecraft:Poison", "Poison", "bad")
    WITHER = (19, "minecraft:Wither", "Wither", "bad")
    HEALTHBOOST = (20, "minecraft:HealthBoost", "Health Boost", "good")
    ABSORPTION = (21, "minecraft:Absorption", "Absorption", "good")
    SATURATION = (22, "minecraft:Saturation", "Saturation", "good")
    GLOWING = (23, "minecraft:Glowing", "Glowing", "bad")
    LEVITATION = (24, "minecraft:Levitation", "Levitation", "bad")
    LUCK = (25, "minecraft:Luck", "Luck", "good")
    BADLUCK = (26, "minecraft:BadLuck", "Bad Luck", "bad")
    SLOWFALLING = (27, "minecraft:SlowFalling", "Slow Falling", "good")
    CONDUITPOWER = (28, "minecraft:ConduitPower", "Conduit Power", "good")
    DOLPHINSGRACE = (29, "minecraft:DolphinsGrace", "Dolphin's Grace", "good")
    BADOMEN = (30, "minecraft:BadOmen", "Bad Omen", "bad")
    HEROOFTHEVILLAGE = (31, "minecraft:HeroOfTheVillage", "Hero of the Village", "good")
    DARKNESS = (32, "minecraft:Darkness", "Darkness", "bad")
    TRIALOMEN = (33, "minecraft:TrialOmen", "Trial Omen", "bad")
    RAIDOMEN = (34, "minecraft:RaidOmen", "Raid Omen", "bad")
    WINDCHARGED = (35, "minecraft:WindCharged", "Wind Charged", "bad")
    WEAVING = (36, "minecraft:Weaving", "Weaving", "bad")
    OOZING = (37, "minecraft:Oozing", "Oozing", "bad")
    INFESTED = (38, "minecraft:Infested", "Infested", "bad")
    BREATHOFTHENAUTILUS = (39, "minecraft:BreathOfTheNautilus", "Breath of the Nautilus", "good")
