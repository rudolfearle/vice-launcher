import json
import os
import shutil
import sys
from datetime import datetime, timezone

# Config lives in the standard per-user config dir (~/.config/vice-launcher
# by default). This can't be "next to main.py" -- when packaged with
# PyInstaller (onefile), __file__ resolves into a temp extraction dir that's
# wiped after every run, which would silently lose all settings each launch.
_XDG_CONFIG_HOME = os.environ.get("XDG_CONFIG_HOME") or os.path.join(
    os.path.expanduser("~"), ".config"
)
CONFIG_PATH = os.environ.get(
    "VICE_LAUNCHER_CONFIG",
    os.path.join(_XDG_CONFIG_HOME, "vice-launcher", "config.json"),
)

# Where config.json used to live (project root, next to main.py) before the
# move to the XDG path above. Only used to migrate an existing dev install's
# settings the first time the new path is missing.
if getattr(sys, "frozen", False):
    _LEGACY_CONFIG_PATH = None
else:
    _LEGACY_CONFIG_PATH = os.path.normpath(
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
    "joydev1": 0,                 # VICE -joydev1 device code (0 = None)
    "joydev2": 0,                  # VICE -joydev2 device code (0 = None)
}


def _migrate_legacy_config():
    if not _LEGACY_CONFIG_PATH or not os.path.exists(_LEGACY_CONFIG_PATH):
        return
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    shutil.copyfile(_LEGACY_CONFIG_PATH, CONFIG_PATH)


def load_config():
    if not os.path.exists(CONFIG_PATH):
        _migrate_legacy_config()

    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r") as f:
            data = json.load(f)
        cfg = DEFAULT_CONFIG.copy()
        cfg.update(data)
        return cfg
    return DEFAULT_CONFIG.copy()


def save_config(cfg):
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
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
