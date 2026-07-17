"""Auto-generated from PrismarineJS/minecraft-data.
Minecraft Java Edition 1.21.11 — 65 biome types.

Each member's .value is the integer registry id for this version;
.string_id is the namespaced id (e.g. 'minecraft:plains').
.display_name is the human label.
.category groups them (e.g. 'plains').
.dimension is 'overworld'/'nether'/'end'.
NOTE: numeric ids are stable within a version but change between
versions (Java has no permanent numeric ids since 1.13).
Do not edit by hand; regenerate with _generate/biomes.py."""

from enum import Enum


class Biome(Enum):
    def __new__(cls, num_id, string_id, display_name, category, dimension):
        obj = object.__new__(cls)
        obj._value_ = num_id
        obj.string_id = string_id
        obj.display_name = display_name
        obj.category = category
        obj.dimension = dimension
        return obj

    BADLANDS = (0, "minecraft:badlands", "Badlands", "mesa", "overworld")
    BAMBOO_JUNGLE = (1, "minecraft:bamboo_jungle", "Bamboo Jungle", "jungle", "overworld")
    BASALT_DELTAS = (2, "minecraft:basalt_deltas", "Basalt Deltas", "nether", "nether")
    BEACH = (3, "minecraft:beach", "Beach", "beach", "overworld")
    BIRCH_FOREST = (4, "minecraft:birch_forest", "Birch Forest", "forest", "overworld")
    CHERRY_GROVE = (5, "minecraft:cherry_grove", "Cherry Grove", "forest", "overworld")
    COLD_OCEAN = (6, "minecraft:cold_ocean", "Cold Ocean", "ocean", "overworld")
    CRIMSON_FOREST = (7, "minecraft:crimson_forest", "Crimson Forest", "nether", "nether")
    DARK_FOREST = (8, "minecraft:dark_forest", "Dark Forest", "forest", "overworld")
    DEEP_COLD_OCEAN = (9, "minecraft:deep_cold_ocean", "Deep Cold Ocean", "ocean", "overworld")
    DEEP_DARK = (10, "minecraft:deep_dark", "Deep Dark", "underground", "overworld")
    DEEP_FROZEN_OCEAN = (11, "minecraft:deep_frozen_ocean", "Deep Frozen Ocean", "ocean", "overworld")
    DEEP_LUKEWARM_OCEAN = (12, "minecraft:deep_lukewarm_ocean", "Deep Lukewarm Ocean", "ocean", "overworld")
    DEEP_OCEAN = (13, "minecraft:deep_ocean", "Deep Ocean", "ocean", "overworld")
    DESERT = (14, "minecraft:desert", "Desert", "desert", "overworld")
    DRIPSTONE_CAVES = (15, "minecraft:dripstone_caves", "Dripstone Caves", "underground", "overworld")
    END_BARRENS = (16, "minecraft:end_barrens", "End Barrens", "the_end", "end")
    END_HIGHLANDS = (17, "minecraft:end_highlands", "End Highlands", "the_end", "end")
    END_MIDLANDS = (18, "minecraft:end_midlands", "End Midlands", "the_end", "end")
    ERODED_BADLANDS = (19, "minecraft:eroded_badlands", "Eroded Badlands", "mesa", "overworld")
    FLOWER_FOREST = (20, "minecraft:flower_forest", "Flower Forest", "forest", "overworld")
    FOREST = (21, "minecraft:forest", "Forest", "forest", "overworld")
    FROZEN_OCEAN = (22, "minecraft:frozen_ocean", "Frozen Ocean", "ocean", "overworld")
    FROZEN_PEAKS = (23, "minecraft:frozen_peaks", "Frozen Peaks", "ice", "overworld")
    FROZEN_RIVER = (24, "minecraft:frozen_river", "Frozen River", "ice", "overworld")
    GROVE = (25, "minecraft:grove", "Grove", "forest", "overworld")
    ICE_SPIKES = (26, "minecraft:ice_spikes", "Ice Spikes", "ice", "overworld")
    JAGGED_PEAKS = (27, "minecraft:jagged_peaks", "Jagged Peaks", "mountain", "overworld")
    JUNGLE = (28, "minecraft:jungle", "Jungle", "jungle", "overworld")
    LUKEWARM_OCEAN = (29, "minecraft:lukewarm_ocean", "Lukewarm Ocean", "ocean", "overworld")
    LUSH_CAVES = (30, "minecraft:lush_caves", "Lush Caves", "underground", "overworld")
    MANGROVE_SWAMP = (31, "minecraft:mangrove_swamp", "Mangrove Swamp", "forest", "overworld")
    MEADOW = (32, "minecraft:meadow", "Meadow", "mountain", "overworld")
    MUSHROOM_FIELDS = (33, "minecraft:mushroom_fields", "Mushroom Fields", "mushroom", "overworld")
    NETHER_WASTES = (34, "minecraft:nether_wastes", "Nether Wastes", "nether", "nether")
    OCEAN = (35, "minecraft:ocean", "Ocean", "ocean", "overworld")
    OLD_GROWTH_BIRCH_FOREST = (36, "minecraft:old_growth_birch_forest", "Old Growth Birch Forest", "forest", "overworld")
    OLD_GROWTH_PINE_TAIGA = (37, "minecraft:old_growth_pine_taiga", "Old Growth Pine Taiga", "taiga", "overworld")
    OLD_GROWTH_SPRUCE_TAIGA = (38, "minecraft:old_growth_spruce_taiga", "Old Growth Spruce Taiga", "taiga", "overworld")
    PALE_GARDEN = (39, "minecraft:pale_garden", "Pale Garden", "none", "overworld")
    PLAINS = (40, "minecraft:plains", "Plains", "plains", "overworld")
    RIVER = (41, "minecraft:river", "River", "river", "overworld")
    SAVANNA = (42, "minecraft:savanna", "Savanna", "savanna", "overworld")
    SAVANNA_PLATEAU = (43, "minecraft:savanna_plateau", "Savanna Plateau", "savanna", "overworld")
    SMALL_END_ISLANDS = (44, "minecraft:small_end_islands", "Small End Islands", "the_end", "end")
    SNOWY_BEACH = (45, "minecraft:snowy_beach", "Snowy Beach", "beach", "overworld")
    SNOWY_PLAINS = (46, "minecraft:snowy_plains", "Snowy Plains", "plains", "overworld")
    SNOWY_SLOPES = (47, "minecraft:snowy_slopes", "Snowy Slopes", "mountain", "overworld")
    SNOWY_TAIGA = (48, "minecraft:snowy_taiga", "Snowy Taiga", "taiga", "overworld")
    SOUL_SAND_VALLEY = (49, "minecraft:soul_sand_valley", "Soul Sand Valley", "nether", "nether")
    SPARSE_JUNGLE = (50, "minecraft:sparse_jungle", "Sparse Jungle", "jungle", "overworld")
    STONY_PEAKS = (51, "minecraft:stony_peaks", "Stony Peaks", "mountain", "overworld")
    STONY_SHORE = (52, "minecraft:stony_shore", "Stony Shore", "beach", "overworld")
    SUNFLOWER_PLAINS = (53, "minecraft:sunflower_plains", "Sunflower Plains", "plains", "overworld")
    SWAMP = (54, "minecraft:swamp", "Swamp", "swamp", "overworld")
    TAIGA = (55, "minecraft:taiga", "Taiga", "taiga", "overworld")
    THE_END = (56, "minecraft:the_end", "The End", "the_end", "end")
    THE_VOID = (57, "minecraft:the_void", "The Void", "none", "overworld")
    WARM_OCEAN = (58, "minecraft:warm_ocean", "Warm Ocean", "ocean", "overworld")
    WARPED_FOREST = (59, "minecraft:warped_forest", "Warped Forest", "nether", "nether")
    WINDSWEPT_FOREST = (60, "minecraft:windswept_forest", "Windswept Forest", "forest", "overworld")
    WINDSWEPT_GRAVELLY_HILLS = (61, "minecraft:windswept_gravelly_hills", "Windswept Gravelly Hills", "extreme_hills", "overworld")
    WINDSWEPT_HILLS = (62, "minecraft:windswept_hills", "Windswept Hills", "extreme_hills", "overworld")
    WINDSWEPT_SAVANNA = (63, "minecraft:windswept_savanna", "Windswept Savanna", "savanna", "overworld")
    WOODED_BADLANDS = (64, "minecraft:wooded_badlands", "Wooded Badlands", "mesa", "overworld")
