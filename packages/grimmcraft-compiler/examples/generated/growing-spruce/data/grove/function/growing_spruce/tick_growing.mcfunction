# Tick while in GROWING
scoreboard players add spruce spruce_stage 1
execute if score spruce spruce_stage matches 1 run fill 0 64 0 0 69 0 minecraft:spruce_log
execute if score spruce spruce_stage matches 2 run fill -2 66 -2 2 66 2 minecraft:spruce_leaves keep
execute if score spruce spruce_stage matches 3 run fill -2 67 -2 2 67 2 minecraft:spruce_leaves keep
execute if score spruce spruce_stage matches 4 run fill -1 68 -1 1 68 1 minecraft:spruce_leaves keep
execute if score spruce spruce_stage matches 5 run fill -1 69 -1 1 69 1 minecraft:spruce_leaves keep
execute if score spruce spruce_stage matches 6 run fill -1 70 -1 1 70 1 minecraft:spruce_leaves keep
execute if score spruce spruce_stage matches 7 run fill 0 71 0 0 71 0 minecraft:spruce_leaves keep
execute if score spruce spruce_stage matches 7 run function grove:growing_spruce/do_growing__tick__grown
