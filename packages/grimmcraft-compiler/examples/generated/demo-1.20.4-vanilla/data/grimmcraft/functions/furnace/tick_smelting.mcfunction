# Tick while in SMELTING
scoreboard players add furnace furnace_timer -1
execute if score furnace furnace_timer matches 0 run function grimmcraft:furnace/do_smelting__tick__done
