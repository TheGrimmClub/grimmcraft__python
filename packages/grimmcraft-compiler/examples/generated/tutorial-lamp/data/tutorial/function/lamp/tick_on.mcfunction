# Tick while in ON
scoreboard players add lamp lamp_timer -1
execute if score lamp lamp_timer matches 0 run function tutorial:lamp/do_on__tick__off
