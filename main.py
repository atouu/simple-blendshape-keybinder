import sys, tomllib, textwrap, time
from pythonosc.udp_client import SimpleUDPClient
from functools import partial
from pynput import keyboard, mouse
from pathlib import Path

blend_states = {}

def send_blend(client, name, value):
    client.send_message("/VMC/Ext/Blend/Val", [name, float(value)])

def apply_blends(client):
    client.send_message("/VMC/Ext/Blend/Apply", [])

def on_mouse_move(client, max_xy, x, y):
    norm_x = clamp(x / max_xy[0])
    norm_y = clamp(y / max_xy[1])
    send_blend(client, "mouse_pos_x", norm_x)
    send_blend(client, "mouse_pos_y", norm_y)
    apply_blends(client)

def toggle_blend(client, blendshape):
    blend_states[blendshape] = 1 - blend_states[blendshape]
    send_blend(client, blendshape, blend_states[blendshape])
    apply_blends(client)
    print(f"{blendshape} = {blend_states[blendshape]}")

def clamp(value):
    return max(0.0, min(1.0, value))

def load_config(config_file):
    if config_file.exists():
        with open(config_file, "rb") as f:
            config = tomllib.load(f)
    else:
        config_template = textwrap.dedent("""\
            vmc_ip = "127.0.0.1"
            vmc_port = 39539
            initialize = false # Run each keystrokes on start
            
            [mouse]
            enabled = false
            max_xy = [1920, 1080] # Monitor resolution
            
            [keystrokes]
            # "<keystroke>" = ["<blendshape_name>", <initial_value>]
            "<ctrl>+<alt>+m" = [ "meow_toggle", 0 ]
        """)
        open(config_file, "x").write(config_template)
        config = tomllib.loads(config_template)

    return config

def main():
    if getattr(sys, 'frozen', False):
        script_dir = Path(sys.executable).resolve().parent
    else:
        script_dir = Path(__file__).resolve().parent

    config = load_config(Path(sys.argv[1]) if len(sys.argv) == 2 else script_dir.joinpath("config.toml"))
    client = SimpleUDPClient(config["vmc_ip"], config["vmc_port"])
    toggles_lambda = {}

    for key in config["keystrokes"]:
        blendshape = config["keystrokes"][key][0]
        blend_states[blendshape] = config["keystrokes"][key][1]
        toggles_lambda[key] = partial(toggle_blend, client,  blendshape)
    
    if config["initialize"]:
        for value in toggles_lambda.values():
            value()
            
    if config["mouse"]["enabled"]:
        mouse.Listener(on_move=partial(on_mouse_move, client, config["mouse"]["max_xy"])).start()
    
    with keyboard.GlobalHotKeys(toggles_lambda) as k:
        k.join()

if __name__ == "__main__":
    main()