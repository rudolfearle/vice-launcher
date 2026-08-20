import os

# File types VICE can autostart directly
SUPPORTED_EXTENSIONS = {
    ".d64", ".d71", ".d81", ".g64",   # disk images
    ".t64", ".tap",                    # tape images
    ".prg", ".p00",                    # programs
    ".crt",                            # cartridges
    ".zip",                            # zipped images (VICE can open these directly)
}

# Folder names to skip during a scan (case-insensitive): machine/drive BIOS
# dumps, our own cover-art storage, and a review folder for flagged
# duplicate/near-duplicate games -- none of these hold real games.
EXCLUDED_DIR_NAMES = {"bios", "images", "dublicates", "duplicates"}


def scan_games(games_dir):
    """Walk games_dir recursively and return a sorted, de-duplicated list of
    game entries.

    The same title sometimes exists in more than one subfolder (e.g. a disk
    image and a separately-collected tape image of the same game) -- only
    the first one encountered is kept, so each title is listed once.
    Directory traversal order is sorted for reproducible results.

    Each entry is a dict: {"path": ..., "title": ..., "ext": ...}
    """
    games = []
    seen_titles = set()
    if not games_dir or not os.path.isdir(games_dir):
        return games

    for root, dirs, files in os.walk(games_dir):
        dirs[:] = sorted(d for d in dirs if d.lower() not in EXCLUDED_DIR_NAMES)
        for name in sorted(files):
            ext = os.path.splitext(name)[1].lower()
            if ext not in SUPPORTED_EXTENSIONS:
                continue
            title = os.path.splitext(name)[0]
            if title in seen_titles:
                continue
            seen_titles.add(title)
            full_path = os.path.join(root, name)
            games.append({
                "path": full_path,
                "title": title,
                "ext": ext,
            })

    games.sort(key=lambda g: g["title"].lower())
    return games
