# Handle event 'pull'
execute if score lamp grimmcraft_state matches 0 run function tutorial:lamp/do_off__pull__on
execute if score lamp grimmcraft_state matches 1 run function tutorial:lamp/do_on__pull__off
