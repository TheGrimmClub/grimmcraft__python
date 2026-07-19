tellraw @a ["",{"text":"Loading Fireworks...","color":"green"}]
scoreboard objectives add Feuerwerk dummy
scoreboard players add timer Feuerwerk 100
scoreboard players set timer Feuerwerk 100
scoreboard objectives setdisplay sidebar Feuerwerk

tellraw @a ["",{"text":"done","color":"green"}]
