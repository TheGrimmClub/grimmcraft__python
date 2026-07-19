# OFF --pull--> ON
scoreboard players set lamp grimmcraft_state 1
setblock 0 64 0 minecraft:light[level=15]
playsound minecraft:block.lever.click master @a
say The lamp glows.
scoreboard players set lamp lamp_timer 100
