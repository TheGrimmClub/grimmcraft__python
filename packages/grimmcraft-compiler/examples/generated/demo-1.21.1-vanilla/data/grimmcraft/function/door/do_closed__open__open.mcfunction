# CLOSED --open--> OPEN
say The door creaks open.
scoreboard players set door grimmcraft_state 1
setblock 0 65 0 minecraft:redstone_lamp[lit=true]
playsound minecraft:block.wooden_door.open master @a
