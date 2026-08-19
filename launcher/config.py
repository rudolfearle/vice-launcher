import json
import os

# config.json lives at the project root, next to main.py
CONFIG_PATH = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "config.json")
)

DEFAULT_CONFIG = {
    "vice_bin_dir": "",     # folder containing x64sc etc. Leave blank to search PATH.
    "vice_flatpak": False,  # True if VICE was installed via Flathub (net.sf.VICE)
    "games_dir": "",        # folder to scan for game images
    "default_machine": "x64sc",
}


def load_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r") as f:
            data = json.load(f)
        cfg = DEFAULT_CONFIG.copy()
        cfg.update(data)
        return cfg
    return DEFAULT_CONFIG.copy()


def save_config(cfg):
    with open(CONFIG_PATH, "w") as f:
        json.dump(cfg, f, indent=2)
