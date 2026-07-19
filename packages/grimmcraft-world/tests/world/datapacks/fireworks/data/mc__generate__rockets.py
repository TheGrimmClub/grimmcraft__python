# mc__generate__rockets.py
# used by Draft [[= Minecraft Feuerwerk \/ Fireworks]]
from pathlib import Path
import logging
from rich.logging import RichHandler
import random

# Define a global dictionary for colors and fade colors
COLOR_DICT = {
    "blue": (0x0000A0, 0xDDEEFF),
    "red": (0xFF0000, 0xFFAAAA),
    "green": (0x00FF00, 0xAAFFAA),
    "yellow": (0xFFFF00, 0xFFFFAA),
    "purple": (0x800080, 0xE6A0FF),
    "orange": (0xFFA500, 0xFFD8A5),
    "pink": (0xFFC0CB, 0xFFB6C1),
    "cyan": (0x00FFFF, 0xA5FFFF),
    "white": (0xFFFFFF, 0xF0F0F0),
    "light_blue": (0xADD8E6, 0xB0E0E6),
    # Add more colors as needed
}

# Set up logging with RichHandler
logging.basicConfig(level=logging.INFO, format="%(message)s", handlers=[RichHandler()])
logger = logging.getLogger("rich")

def generate_rocket_function(rocket_name: str, shape: str, color_name: str, flight_duration: int) -> str:
    """
    Generate the content for a firework rocket mcfunction using a color from the global dictionary.
    
    :param rocket_name: The name of the rocket function (e.g., 'rocket_blue_star').
    :param shape: The explosion shape of the firework (e.g., 'star', 'burst').
    :param color_name: The color name (e.g., 'blue').
    :param flight_duration: The flight duration of the firework (1 to 3).
    :return: Minecraft function content as a string.
    """
    # Get the color and fade color from the COLOR_DICT
    color, fade_color = COLOR_DICT[color_name]

    # Generate the function content with the selected color and fade color
    return f'''summon firework_rocket ~ ~1 ~ {{LifeTime:45,FireworksItem:{{id:firework_rocket,count:1,components:{{fireworks:{{flight_duration:{flight_duration},explosions:[{{shape:"{shape}",colors:[I;{color}],fade_colors:[I;{fade_color}],has_twinkle:0,has_trail:0}}]}}}}}}}}}}'''

def generate_rockets():
    # Define paths
    datapack_name = "fireworks"
    datapack_path = Path(datapack_name)
    functions_folder = datapack_path / "function"
    
    # Create the necessary folder
    functions_folder.mkdir(parents=True, exist_ok=True)
    
    # Rocket shapes and flight durations
    shapes = ["star", "burst", "ball", "creeper", "sparkler"]
    flight_durations = [1, 2, 3]
    color_names = list(COLOR_DICT.keys())  # Extract all color names from the dictionary
    
    # Generate 42 rocket functions with unique names and properties
    for i in range(42):
        # Randomly pick a shape, color, and flight duration
        shape = random.choice(shapes)
        color_name = random.choice(color_names)
        flight_duration = random.choice(flight_durations)
        
        # Create a unique rocket name based on the color, shape, and flight duration
        rocket_name = f"rocket_{color_name}_{shape}_{flight_duration}"
        
        # Generate the function content
        rocket_content = generate_rocket_function(rocket_name, shape, color_name, flight_duration)
        
        # Save the function to a .mcfunction file
        function_file_path = functions_folder / f"{rocket_name}.mcfunction"
        function_file_path.write_text(rocket_content)
        
        # Log success
        logger.info(f"Generated rocket function: {rocket_name}.mcfunction")

        # Add the function definition in minecraft/tags/function
        # with open(datapack_path / "data" / "minecraft" / "tags" / "function" / "load.json", "a") as f:
        #    f.write(f'"fireworks:{rocket_name}",\n')
        #
        json_path = Path("minecraft") / "tags" / "function" / f"{rocket_name}.json"
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(f'{{ "values": [ "fireworks:{rocket_name}" ] }}')

    logger.info("success 42 rocket functions generated successfully!")

if __name__ == "__main__":
    generate_rockets()