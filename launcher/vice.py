import os
import shutil
import subprocess

# Default machine binary per file extension.
# Nearly everything floating around is C64, so we default to x64sc
# (the accurate C64 core) unless a game entry overrides "machine".
EXTENSION_MACHINE = {
    ".d64": "x64sc", ".d71": "x64sc", ".d81": "x64sc", ".g64": "x64sc",
    ".t64": "x64sc", ".tap": "x64sc",
    ".prg": "x64sc", ".p00": "x64sc",
    ".crt": "x64sc",
    ".zip": "x64sc",
}

MACHINES = ["x64sc", "x128", "xvic", "xplus4", "xpet", "xcbm2"]


def machine_for_extension(ext):
    return EXTENSION_MACHINE.get(ext.lower(), "x64sc")


def resolve_binary(cfg, machine):
    """Return the base command (a list) used to invoke the given VICE machine."""
    if cfg.get("vice_flatpak"):
        return ["flatpak", "run", "--command=" + machine, "net.sf.VICE"]

    bin_dir = cfg.get("vice_bin_dir") or ""
    if bin_dir:
        candidate = os.path.join(bin_dir, machine)
        if os.path.exists(candidate):
            return [candidate]

    found = shutil.which(machine)
    if found:
        return [found]

    return None


def launch_game(cfg, game):
    """Launch a game entry via VICE. Returns the Popen object."""
    machine = game.get("machine") or machine_for_extension(game["ext"])
    command = resolve_binary(cfg, machine)
    if command is None:
        raise FileNotFoundError(
            f"Could not find the VICE binary '{machine}'.\n\n"
            f"Fix this via File > Set VICE Binary Folder, or, if you installed "
            f"VICE through Flathub, enable File > Use Flatpak VICE instead."
        )
    full_command = command + ["-autostart", game["path"]]
    return subprocess.Popen(full_command)
