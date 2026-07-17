# EMPTY --insert_ore--> SMELTING
setblock 3 64 0 minecraft:furnace[lit=true]
scoreboard players set furnace grimmcraft_state 1
say The furnace roars to life.
playsound minecraft:block.furnace.fire_crackle master @a
scoreboard players set furnace furnace_timer 200
