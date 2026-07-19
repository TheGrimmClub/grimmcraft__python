from pathlib import Path

function_path = Path("fireworks") / "function" 





# list all '*.mcfunction' files in the 'fireworks/function' folder


print(f'files')
for file in function_path.glob("*.mcfunction"):

        # output file 
        rocket_name = file.stem
        print(rocket_name)

        # generates tags 
        if rocket_name.find("rocket") >= 0:
            timer_path = Path("fireworks") / "function" / f"{rocket_name}.mcfunction".replace("rocket", "timer")

            print(timer_path)

            if not timer_path.exists():
                print("new file found")

                timer_path.parent.mkdir(parents=True, exist_ok=True)
                

                with open(file, "r") as f:
                    data = f.read()
                    data = data.replace("summon firework_rocket ~ ~2 ~ ", "")

                print(data)

                functions = f"""execute if score timer Feuerwerk matches 80 run summon firework_rocket ~5 ~1 ~ {data}
execute if score timer Feuerwerk matches 60 run summon firework_rocket ~10 ~1 ~ {data}
execute if score timer Feuerwerk matches 40 run summon firework_rocket ~5 ~1 ~ {data}
execute if score timer Feuerwerk matches 20 run summon firework_rocket ~10 ~1 ~ {data}
execute if score timer Feuerwerk matches 0 run summon firework_rocket ~5 ~1 ~ {data}
"""
                timer_path.write_text(functions)
