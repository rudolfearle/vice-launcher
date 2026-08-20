import os
import shutil
import subprocess
import tempfile
import zipfile

from . import scanner

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

# Which native joystick ports (-joydev1, -joydev2) each machine binary supports.
# PET and CBM-II have no native joystick ports (userport adapters only), and the
# VIC-20 has just one.
JOYSTICK_PORTS = {
    "x64sc": (True, True),
    "x128": (True, True),
    "xvic": (True, False),
    "xplus4": (True, True),
    "xpet": (False, False),
    "xcbm2": (False, False),
}


def machine_for_extension(ext, cfg=None):
    default = cfg.get("default_machine", "x64sc") if cfg else "x64sc"
    return EXTENSION_MACHINE.get(ext.lower(), default)


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


def _extract_zip_entry(zip_path):
    """Extract the first supported game file found inside a zip to a temp dir.

    Returns the extracted file's path, or None if the zip couldn't be read
    or contains nothing VICE can autostart directly.
    """
    inner_extensions = scanner.SUPPORTED_EXTENSIONS - {".zip"}
    try:
        with zipfile.ZipFile(zip_path) as zf:
            candidates = sorted(
                name for name in zf.namelist()
                if not name.endswith("/")
                and os.path.splitext(name)[1].lower() in inner_extensions
            )
            if not candidates:
                return None
            member = candidates[0]
            dest_dir = tempfile.mkdtemp(prefix="vice_launcher_")
            zf.extract(member, dest_dir)
            return os.path.join(dest_dir, member)
    except (zipfile.BadZipFile, OSError):
        return None


def launch_game(cfg, game):
    """Launch a game entry via VICE. Returns the Popen object."""
    machine_override = (cfg.get("machine_overrides") or {}).get(game["path"])
    launch_path = game["path"]
    ext = game["ext"]

    if ext == ".zip":
        # VICE can usually open zips directly, but some builds/archive layouts
        # choke on it. Extracting the inner image ourselves is a reliable fallback.
        extracted = _extract_zip_entry(game["path"])
        if extracted:
            launch_path = extracted
            ext = os.path.splitext(extracted)[1].lower()

    machine = machine_override or machine_for_extension(ext, cfg)
    command = resolve_binary(cfg, machine)
    if command is None:
        raise FileNotFoundError(
            f"Could not find the VICE binary '{machine}'.\n\n"
            f"Fix this via File > Preferences, or, if you installed "
            f"VICE through Flathub, enable the Flatpak VICE option there instead."
        )
    joystick_args = []
    supports_port1, supports_port2 = JOYSTICK_PORTS.get(machine, (True, True))
    if supports_port1:
        joystick_args += ["-joydev1", str(cfg.get("joydev1", 0))]
    if supports_port2:
        joystick_args += ["-joydev2", str(cfg.get("joydev2", 0))]

    full_command = command + joystick_args + ["-autostart", launch_path]
    return subprocess.Popen(full_command)
