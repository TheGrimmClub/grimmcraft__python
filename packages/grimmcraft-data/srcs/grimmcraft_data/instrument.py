"""Auto-generated from PrismarineJS/minecraft-data.
Minecraft Java Edition 1.21.11 — 23 instrument types.

Each member's .value is the integer registry id for this version;
.string_id is the namespaced id (e.g. 'minecraft:harp').
NOTE: numeric ids are stable within a version but change between
versions (Java has no permanent numeric ids since 1.13).
Do not edit by hand; regenerate with _generate/instruments.py."""

from __future__ import annotations

from grimmclub_standardlib import Enum


class Instrument(Enum):
    string_id: str

    def __new__(cls, num_id: int, string_id: str) -> Instrument:
        obj = object.__new__(cls)
        obj._value_ = num_id
        obj.string_id = string_id
        return obj

    HARP = (0, "minecraft:harp")
    BASEDRUM = (1, "minecraft:basedrum")
    SNARE = (2, "minecraft:snare")
    HAT = (3, "minecraft:hat")
    BASS = (4, "minecraft:bass")
    FLUTE = (5, "minecraft:flute")
    BELL = (6, "minecraft:bell")
    GUITAR = (7, "minecraft:guitar")
    CHIME = (8, "minecraft:chime")
    XYLOPHONE = (9, "minecraft:xylophone")
    IRON_XYLOPHONE = (10, "minecraft:iron_xylophone")
    COW_BELL = (11, "minecraft:cow_bell")
    DIDGERIDOO = (12, "minecraft:didgeridoo")
    BIT = (13, "minecraft:bit")
    BANJO = (14, "minecraft:banjo")
    PLING = (15, "minecraft:pling")
    ZOMBIE = (16, "minecraft:zombie")
    SKELETON = (17, "minecraft:skeleton")
    CREEPER = (18, "minecraft:creeper")
    DRAGON = (19, "minecraft:dragon")
    WITHER_SKELETON = (20, "minecraft:wither_skeleton")
    PIGLIN = (21, "minecraft:piglin")
    CUSTOM_HEAD = (22, "minecraft:custom_head")
