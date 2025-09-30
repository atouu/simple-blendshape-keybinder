from pythonosc.udp_client import SimpleUDPClient
from functools import partial
from pynput import keyboard
from pathlib import Path
import sys
import tomllib
import textwrap
import time

blend_states = {}

def send_blend(client, name, value):
    client.send_message("/VMC/Ext/Blend/Val", [name, float(value)])

def apply_blends(client):
    client.send_message("/VMC/Ext/Blend/Apply", [])


def toggle_blend(client, blendshape):
    blend_states[blendshape] = 1 - blend_states[blendshape]
    send_blend(client, blendshape, blend_states[blendshape])
    apply_blends(client)
    print(f"{blendshape} = {blend_states[blendshape]}")

def load_config(config_file):
    if config_file.exists():
        with open(config_file, "rb") as f:
            config = tomllib.load(f)
    else:
        config_template = textwrap.dedent("""\
            vmc_ip = "127.0.0.1"
            vmc_port = 39539

            [toggles]
            "<ctrl>+<alt>+m" = "meow_toggle"
            # "<keystroke>" = "blendshape_name"
        """)
        open(config_file, "x").write(config_template)
        config = tomllib.loads(config_template)

    return (
        config["vmc_ip"],
        config["vmc_port"],
        config["toggles"]
    )

def main():
    if getattr(sys, 'frozen', False):
        script_dir = Path(sys.executable).resolve().parent
    else:
        script_dir = Path(__file__).resolve().parent

    vmc_ip, vmc_port, toggles = load_config(script_dir.joinpath("config.toml"))
    
    client = SimpleUDPClient(vmc_ip, vmc_port)
    
    toggles_lambda = {}

    for key in toggles:
        blendshape = toggles[key]
        blend_states[blendshape] = 1
        toggles_lambda[key] = partial(toggle_blend, client,  blendshape)

    with keyboard.GlobalHotKeys(toggles_lambda) as k:
        k.join()

if __name__ == "__main__":
    main()