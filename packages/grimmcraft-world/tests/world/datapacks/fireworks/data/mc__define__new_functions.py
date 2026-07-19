from pathlib import Path

function_path = Path("fireworks") / "function" 

# list all '*.mcfunction' files in the 'fireworks/function' folder


print(f'files')
for file in function_path.glob("*.mcfunction"):

        # output file 
        rocket_name = file.stem
        print(rocket_name)

        # generates tags 
        json_path = Path("minecraft") / "tags" / "function" / f"{rocket_name}.json"
        if not json_path.exists():
            json_path.parent.mkdir(parents=True, exist_ok=True)
            json_path.write_text(f'{{ "values": [ "fireworks:{rocket_name}" ] }}')
