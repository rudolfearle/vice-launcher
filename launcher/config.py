import json
import os
from datetime import datetime, timezone

# config.json lives at the project root, next to main.py
CONFIG_PATH = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "config.json")
)

RECENT_LIMIT = 20

DEFAULT_CONFIG = {
    "vice_bin_dir": "",     # folder containing x64sc etc. Leave blank to search PATH.
    "vice_flatpak": False,  # True if VICE was installed via Flathub (net.sf.VICE)
    "games_dir": "",        # folder to scan for game images
    "default_machine": "x64sc",
    "favorites": [],           # list of game paths
    "recent": [],               # list of {"path": ..., "ts": iso timestamp}, newest first
    "machine_overrides": {},     # {path: machine}
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


def is_favorite(cfg, path):
    return path in cfg.get("favorites", [])


def toggle_favorite(cfg, path):
    favorites = cfg.setdefault("favorites", [])
    if path in favorites:
        favorites.remove(path)
    else:
        favorites.append(path)
    save_config(cfg)


def add_recent(cfg, path):
    recent = cfg.setdefault("recent", [])
    recent[:] = [entry for entry in recent if entry.get("path") != path]
    recent.insert(0, {"path": path, "ts": datetime.now(timezone.utc).isoformat()})
    del recent[RECENT_LIMIT:]
    save_config(cfg)


def get_machine_override(cfg, path):
    return cfg.get("machine_overrides", {}).get(path)


def set_machine_override(cfg, path, machine):
    overrides = cfg.setdefault("machine_overrides", {})
    if machine:
        overrides[path] = machine
    else:
        overrides.pop(path, None)
    save_config(cfg)
