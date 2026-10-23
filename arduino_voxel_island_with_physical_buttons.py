import random
import time as clock

import serial
from serial.tools import list_ports

from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController


# =========================================================
# CONFIGURATION
# =========================================================

SERIAL_PORT = "COM7"       # Change to your Arduino COM port
BAUD_RATE = 115200

CENTER_X = 737
CENTER_Y = 741

MIN_X = 0
MAX_X = 1023
MIN_Y = 0
MAX_Y = 1023

DEADZONE = 0.12
TURN_SPEED = 100
WORLD_SIZE = 32           # Expanded world for exploration


# =========================================================
# ARDUINO CONNECTION
# =========================================================

arduino = None

try:
    arduino = serial.Serial(
        SERIAL_PORT,
        BAUD_RATE,
        timeout=0
    )
    clock.sleep(2)
    arduino.reset_input_buffer()
    print(f"Arduino connected on {SERIAL_PORT}")

except (serial.SerialException, OSError) as error:
    print("Arduino connection failed:", error)
    print("Game will run using keyboard & mouse.")


# =========================================================
# URSINA GAME SETUP
# =========================================================

app = Ursina()

window.title = "Arduino Voxel Island - Survival Game"
window.borderless = False
window.fullscreen = False
window.color = color.azure

sky = Sky(color=color.azure)


# =========================================================
# GAME STATE & INVENTORY
# =========================================================

BLOCK_COLORS = {
    "grass": color.rgb(40/255, 180/255, 70/255),
    "dirt":  color.rgb(120/255, 70/255, 30/255),
    "stone": color.rgb(100/255, 105/255, 115/255),
    "wood":  color.rgb(160/255, 90/255, 40/255),
    "sand":  color.rgb(220/255, 190/255, 90/255),
}

BLOCK_TYPES = ["grass", "dirt", "stone", "wood", "sand"]
selected_type_index = 0

# Inventory starts with starter materials
inventory = {
    "grass": 10,
    "dirt": 10,
    "stone": 5,
    "wood": 5,
    "sand": 5
}

# Quests
quest_stage = 0
quests = [
    "QUEST 1: Chop down a Wood tree (Mine 3 Wood blocks)",
    "QUEST 2: Build a basic shelter (Place 5 blocks)",
    "QUEST 3: Mine Stone from the mountain (Mine 5 Stone blocks)",
    "SURVIVAL COMPLETE: Free play / Explore the Island!"
]

blocks_placed = 0
wood_mined = 0
stone_mined = 0

day_time = 0.0


# =========================================================
# BLOCK CLASS
# =========================================================

class Block(Button):
    def __init__(self, position=(0, 0, 0), block_type="grass"):
        super().__init__(
            parent=scene,
            position=position,
            model="cube",
            origin_y=0.5,
            texture=None,
            color=BLOCK_COLORS.get(block_type, color.white),
            highlight_color=color.lime,
            scale=1
        )
        self.block_type = block_type


# =========================================================
# WORLD GENERATION (Hills, Trees, Sand Coasts)
# =========================================================

random.seed(42)

for x in range(WORLD_SIZE):
    for z in range(WORLD_SIZE):

        # Island Coast (Sand) vs Inner Land
        dist_from_center = max(abs(x - WORLD_SIZE/2), abs(z - WORLD_SIZE/2))
        
        if dist_from_center > (WORLD_SIZE / 2) - 3:
            # Water / Beach outline
            Block(position=(x, -1, z), block_type="sand")
            Block(position=(x, 0, z), block_type="sand")
        else:
            # Bedrock
            Block(position=(x, -1, z), block_type="stone")
            # Grass surface
            Block(position=(x, 0, z), block_type="grass")

            # Rolling terrain structures
            rand_val = random.random()

            if rand_val < 0.05:
                # Tree structure
                Block(position=(x, 1, z), block_type="wood")
                Block(position=(x, 2, z), block_type="wood")
                Block(position=(x, 3, z), block_type="wood")
                Block(position=(x, 4, z), block_type="grass")
            elif rand_val < 0.12:
                # Stone hill
                Block(position=(x, 1, z), block_type="stone")
                if random.random() < 0.5:
                    Block(position=(x, 2, z), block_type="stone")


# =========================================================
# PLAYER SETUP
# =========================================================

player = FirstPersonController(
    position=(WORLD_SIZE / 2, 5, WORLD_SIZE / 2),
    speed=6
)

player.gravity = 0.8
player.jump_height = 2


# =========================================================
# ARDUINO INPUT PROCESSING
# =========================================================

move_y = 0.0
turn_x = 0.0

button_down = False
previous_button_down = False

# Two additional physical Arduino buttons
mine_down = False
place_down = False
previous_mine_down = False
previous_place_down = False


def normalise_axis(value, centre, minimum=0, maximum=1023):
    if value >= centre:
        span = maximum - centre
        result = ((value - centre) / span) if span > 0 else 0.0
    else:
        span = centre - minimum
        result = ((value - centre) / span) if span > 0 else 0.0

    result = max(-1.0, min(1.0, result))

    if abs(result) < DEADZONE:
        return 0.0

    if result > 0:
        result = (result - DEADZONE) / (1.0 - DEADZONE)
    else:
        result = (result + DEADZONE) / (1.0 - DEADZONE)

    return result


def read_joystick():
    global move_y, turn_x, button_down, mine_down, place_down

    if arduino is None:
        move_y = 0.0
        turn_x = 0.0
        button_down = False
        mine_down = False
        place_down = False
        return

    try:
        while arduino.in_waiting:
            line = arduino.readline().decode("utf-8", errors="ignore").strip()
            parts = line.split(",")

            # Arduino format: X,Y,JOYSTICK,MINE,PLACE
            if len(parts) != 5:
                continue

            try:
                raw_x = int(parts[0])
                raw_y = int(parts[1])
                raw_button = int(parts[2])
                raw_mine = int(parts[3])
                raw_place = int(parts[4])
            except ValueError:
                continue

            turn_x = normalise_axis(raw_y, CENTER_Y, MIN_Y, MAX_Y)
            move_y = normalise_axis(raw_x, CENTER_X, MIN_X, MAX_X)
            button_down = (raw_button == 0)
            mine_down = (raw_mine == 0)
            place_down = (raw_place == 0)

    except (serial.SerialException, OSError) as error:
        print("Arduino serial error:", error)
        move_y = 0.0
        turn_x = 0.0
        button_down = False
        mine_down = False
        place_down = False


# =========================================================
# MINE & CRAFT MECHANICS
# =========================================================

def mine_block():
    global wood_mined, stone_mined

    target = mouse.hovered_entity
    if not isinstance(target, Block):
        return

    b_type = target.block_type
    inventory[b_type] += 1

    if b_type == "wood":
        wood_mined += 1
    elif b_type == "stone":
        stone_mined += 1

    destroy(target)
    check_quests()
    update_ui()


def place_block():
    global blocks_placed

    target = mouse.hovered_entity
    if not isinstance(target, Block):
        return

    active_type = BLOCK_TYPES[selected_type_index]

    if inventory[active_type] <= 0:
        return

    normal = mouse.normal
    if normal is None:
        return

    new_pos = target.position + normal
    new_pos = Vec3(
        round(new_pos.x),
        round(new_pos.y),
        round(new_pos.z)
    )

    if distance(new_pos, player.position) > 1.5:
        Block(position=new_pos, block_type=active_type)
        inventory[active_type] -= 1
        blocks_placed += 1
        check_quests()
        update_ui()


def input(key):
    global selected_type_index

    # Hotbar selection (keys 1 to 5)
    if key in ("1", "2", "3", "4", "5"):
        selected_type_index = int(key) - 1
        update_ui()

    # Keep the original mouse controls
    elif key == "left mouse down":
        mine_block()

    elif key == "right mouse down":
        place_block()


def check_quests():
    global quest_stage
    if quest_stage == 0 and wood_mined >= 3:
        quest_stage = 1
    elif quest_stage == 1 and blocks_placed >= 5:
        quest_stage = 2
    elif quest_stage == 2 and stone_mined >= 5:
        quest_stage = 3


# =========================================================
# GAME LOOP (DAY/NIGHT CYCLE + MOVEMENT)
# =========================================================

def update():
    global previous_button_down, previous_mine_down
    global previous_place_down, day_time

    read_joystick()

    held_keys["w"] = 1 if move_y > 0 else 0
    held_keys["s"] = 1 if move_y < 0 else 0

    player.rotation_y += (turn_x * TURN_SPEED * time.dt)

    if button_down and not previous_button_down:
        player.jump()

    previous_button_down = button_down

    # Mine/place only once per physical button press
    if mine_down and not previous_mine_down:
        mine_block()

    if place_down and not previous_place_down:
        place_block()

    previous_mine_down = mine_down
    previous_place_down = place_down

    # Gentle Day/Night environment rotation
    day_time += time.dt * 0.02
    if day_time > 1:
        day_time = 0


# =========================================================
# UI & QUEST OVERLAY
# =========================================================

quest_text = Text(
    text="",
    position=(-0.85, 0.45),
    scale=0.9,
    background=True
)

inventory_text = Text(
    text="",
    position=(-0.85, -0.30),
    scale=0.8,
    background=True
)

hotbar_text = Text(
    text="",
    position=(-0.22, -0.42),
    scale=1.0,
    background=True
)


def update_ui():
    # Active quest display
    quest_text.text = (
        f"--- OBJECTIVE ---\n"
        f"{quests[quest_stage]}\n\n"
        f"Joystick: Walk/Turn | Press: Jump\n"
        f"Button D3 / L-Click: Mine\n"
        f"Button D4 / R-Click: Place\n"
        f"Keys 1-5: Select Material"
    )

    # Inventory display
    inventory_text.text = (
        f"--- INVENTORY ---\n"
        f"Grass: {inventory['grass']}\n"
        f"Dirt:  {inventory['dirt']}\n"
        f"Stone: {inventory['stone']}\n"
        f"Wood:  {inventory['wood']}\n"
        f"Sand:  {inventory['sand']}"
    )

    # Hotbar selector display
    active_name = BLOCK_TYPES[selected_type_index].upper()
    hotbar_text.text = (
        f" [1]GRASS [2]DIRT [3]STONE [4]WOOD [5]SAND \n"
        f" Selected to Build: {active_name} ({inventory[BLOCK_TYPES[selected_type_index]]} left) "
    )


update_ui()

# Run application
app.run()
