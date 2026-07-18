# BARE --grow--> GROWN
scoreboard players set tree grimmcraft_state 1
say A tree grows.
fill 0 64 0 0 68 0 minecraft:oak_log
fill -2 67 -2 2 67 2 minecraft:oak_leaves keep
fill -2 68 -2 2 68 2 minecraft:oak_leaves keep
fill -1 69 -1 1 69 1 minecraft:oak_leaves keep
fill -1 70 -1 1 70 1 minecraft:oak_leaves keep
setblock -2 67 -2 minecraft:air
setblock -2 67 2 minecraft:air
setblock 2 67 -2 minecraft:air
setblock 2 67 2 minecraft:air
setblock -2 68 -2 minecraft:air
setblock -2 68 2 minecraft:air
setblock 2 68 -2 minecraft:air
setblock 2 68 2 minecraft:air
