"""Auto-generated from PrismarineJS/minecraft-data.
Minecraft Java Edition 1.21.11 — 44 food types.

Each member's .value is the integer registry id for this version;
.string_id is the namespaced id (e.g. 'minecraft:apple').
.display_name is the human label.
.food_points is hunger restored.
.saturation is saturation restored.
.stack_size is the max stack.
NOTE: numeric ids are stable within a version but change between
versions (Java has no permanent numeric ids since 1.13).
Do not edit by hand; regenerate with _generate/foods.py."""

from enum import Enum


class Food(Enum):
    def __new__(cls, num_id, string_id, display_name, food_points, saturation, stack_size):
        obj = object.__new__(cls)
        obj._value_ = num_id
        obj.string_id = string_id
        obj.display_name = display_name
        obj.food_points = food_points
        obj.saturation = saturation
        obj.stack_size = stack_size
        return obj

    APPLE = (893, "minecraft:apple", "Apple", 4.0, 19.2, 64)
    MUSHROOM_STEW = (947, "minecraft:mushroom_stew", "Mushroom Stew", 6.0, 86.4, 1)
    BREAD = (953, "minecraft:bread", "Bread", 5.0, 60.0, 64)
    PORKCHOP = (983, "minecraft:porkchop", "Raw Porkchop", 3.0, 10.8, 64)
    COOKED_PORKCHOP = (984, "minecraft:cooked_porkchop", "Cooked Porkchop", 8.0, 204.8, 64)
    GOLDEN_APPLE = (986, "minecraft:golden_apple", "Golden Apple", 4.0, 76.8, 64)
    ENCHANTED_GOLDEN_APPLE = (987, "minecraft:enchanted_golden_apple", "Enchanted Golden Apple", 4.0, 76.8, 64)
    PUFFERFISH_BUCKET = (1019, "minecraft:pufferfish_bucket", "Bucket of Pufferfish", 1.0, 0.4, 1)
    SALMON_BUCKET = (1020, "minecraft:salmon_bucket", "Bucket of Salmon", 2.0, 1.6, 1)
    COD_BUCKET = (1021, "minecraft:cod_bucket", "Bucket of Cod", 2.0, 1.6, 1)
    TROPICAL_FISH_BUCKET = (1022, "minecraft:tropical_fish_bucket", "Bucket of Tropical Fish", 1.0, 0.4, 1)
    COD = (1057, "minecraft:cod", "Raw Cod", 2.0, 1.6, 64)
    SALMON = (1058, "minecraft:salmon", "Raw Salmon", 2.0, 1.6, 64)
    TROPICAL_FISH = (1059, "minecraft:tropical_fish", "Tropical Fish", 1.0, 0.4, 64)
    PUFFERFISH = (1060, "minecraft:pufferfish", "Pufferfish", 1.0, 0.4, 64)
    COOKED_COD = (1061, "minecraft:cooked_cod", "Cooked Cod", 5.0, 60.0, 64)
    COOKED_SALMON = (1062, "minecraft:cooked_salmon", "Cooked Salmon", 6.0, 115.200005, 64)
    COOKIE = (1102, "minecraft:cookie", "Cookie", 2.0, 1.6, 64)
    MELON_SLICE = (1106, "minecraft:melon_slice", "Melon Slice", 2.0, 4.8, 64)
    DRIED_KELP = (1107, "minecraft:dried_kelp", "Dried Kelp", 1.0, 1.2, 64)
    BEEF = (1110, "minecraft:beef", "Raw Beef", 3.0, 10.8, 64)
    COOKED_BEEF = (1111, "minecraft:cooked_beef", "Steak", 8.0, 204.8, 64)
    CHICKEN = (1112, "minecraft:chicken", "Raw Chicken", 2.0, 4.8, 64)
    COOKED_CHICKEN = (1113, "minecraft:cooked_chicken", "Cooked Chicken", 6.0, 86.4, 64)
    ROTTEN_FLESH = (1114, "minecraft:rotten_flesh", "Rotten Flesh", 4.0, 6.4, 64)
    SPIDER_EYE = (1122, "minecraft:spider_eye", "Spider Eye", 2.0, 12.8, 64)
    CARROT = (1227, "minecraft:carrot", "Carrot", 3.0, 21.6, 64)
    POTATO = (1228, "minecraft:potato", "Potato", 1.0, 1.2, 64)
    BAKED_POTATO = (1229, "minecraft:baked_potato", "Baked Potato", 5.0, 60.0, 64)
    POISONOUS_POTATO = (1230, "minecraft:poisonous_potato", "Poisonous Potato", 2.0, 4.8, 64)
    GOLDEN_CARROT = (1232, "minecraft:golden_carrot", "Golden Carrot", 6.0, 172.8, 64)
    PUMPKIN_PIE = (1241, "minecraft:pumpkin_pie", "Pumpkin Pie", 8.0, 76.8, 64)
    RABBIT = (1249, "minecraft:rabbit", "Raw Rabbit", 3.0, 10.8, 64)
    COOKED_RABBIT = (1250, "minecraft:cooked_rabbit", "Cooked Rabbit", 5.0, 60.0, 64)
    RABBIT_STEW = (1251, "minecraft:rabbit_stew", "Rabbit Stew", 10.0, 240.0, 1)
    MUTTON = (1264, "minecraft:mutton", "Raw Mutton", 2.0, 4.8, 64)
    COOKED_MUTTON = (1265, "minecraft:cooked_mutton", "Cooked Mutton", 6.0, 115.200005, 64)
    CHORUS_FRUIT = (1283, "minecraft:chorus_fruit", "Chorus Fruit", 4.0, 19.2, 64)
    BEETROOT = (1287, "minecraft:beetroot", "Beetroot", 1.0, 2.4, 64)
    BEETROOT_SOUP = (1289, "minecraft:beetroot_soup", "Beetroot Soup", 6.0, 86.4, 1)
    SUSPICIOUS_STEW = (1340, "minecraft:suspicious_stew", "Suspicious Stew", 6.0, 86.4, 1)
    SWEET_BERRIES = (1373, "minecraft:sweet_berries", "Sweet Berries", 2.0, 1.6, 64)
    GLOW_BERRIES = (1374, "minecraft:glow_berries", "Glow Berries", 2.0, 1.6, 64)
    HONEY_BOTTLE = (1381, "minecraft:honey_bottle", "Honey Bottle", 6.0, 14.400001, 16)
