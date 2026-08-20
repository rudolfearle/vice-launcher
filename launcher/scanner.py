import os

# File types VICE can autostart directly
SUPPORTED_EXTENSIONS = {
    ".d64", ".d71", ".d81", ".g64",   # disk images
    ".t64", ".tap",                    # tape images
    ".prg", ".p00",                    # programs
    ".crt",                            # cartridges
    ".zip",                            # zipped images (VICE can open these directly)
}

# Folder names to skip during a scan (case-insensitive), e.g. machine/drive
# BIOS dumps that live alongside a game collection but aren't games.
EXCLUDED_DIR_NAMES = {"bios"}


def scan_games(games_dir):
    """Walk games_dir recursively and return a sorted list of game entries.

    Each entry is a dict: {"path": ..., "title": ..., "ext": ...}
    """
    games = []
    if not games_dir or not os.path.isdir(games_dir):
        return games

    for root, dirs, files in os.walk(games_dir):
        dirs[:] = [d for d in dirs if d.lower() not in EXCLUDED_DIR_NAMES]
        for name in files:
            ext = os.path.splitext(name)[1].lower()
            if ext in SUPPORTED_EXTENSIONS:
                full_path = os.path.join(root, name)
                title = os.path.splitext(name)[0]
                games.append({
                    "path": full_path,
                    "title": title,
                    "ext": ext,
                })

    games.sort(key=lambda g: g["title"].lower())
    return games
