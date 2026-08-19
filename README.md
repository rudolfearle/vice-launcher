# VICE Game Launcher (Phase 1)

A minimal Tkinter front-end for launching Commodore games through the
[VICE emulator](https://vice-emu.sourceforge.io/).

## Requirements

- Python 3.8+ (Tkinter ships with the standard python3 package on both
  Mint and Fedora — if it's missing: `sudo apt install python3-tk` on
  Mint, `sudo dnf install python3-tkinter` on Fedora)
- VICE installed, via one of:
  - **Mint/Ubuntu:** `sudo apt install vice`
  - **Fedora:** enable RPM Fusion (nonfree), then `sudo dnf install vice`
  - **Either distro:** Flatpak — `flatpak install flathub net.sf.VICE`

## Running

```bash
cd vice-launcher
python3 main.py
```

On first run, use the **File** menu to:
1. **Set Games Folder** — point at the folder holding your game images
   (`.d64`, `.d71`, `.d81`, `.g64`, `.t64`, `.tap`, `.prg`, `.p00`,
   `.crt`, `.zip`), it's scanned recursively.
2. **Set VICE Binary Folder** — point at the folder containing the VICE
   executables (e.g. `x64sc`). If VICE is already on your `PATH`, you
   can skip this — it'll be found automatically.
   - If you installed VICE via Flatpak instead, check **Use Flatpak
     VICE** in the File menu rather than setting a binary folder.

Settings are saved to `config.json` in the project folder, so you only
need to do this once.

Double-click (or select + Enter, or the Launch button) starts the game
via `x64sc -autostart <file>`.

## Current limitations (Phase 1 scope)

- Everything launches with the C64 core (`x64sc`) — no per-game machine
  override yet (VIC-20/C128/Plus4/PET support in `launcher/vice.py` is
  wired up but not yet exposed in the UI).
- No favorites, recently-played, or cover art yet.
- No packaging — this runs from source with `python3 main.py`.

These are the natural next steps for Phase 2 whenever you want to keep
going.

## Project layout

```
vice-launcher/
├── config.json          # created automatically on first save
├── main.py               # entry point
└── launcher/
    ├── config.py          # load/save settings
    ├── scanner.py          # recursive folder scan for game files
    ├── vice.py              # binary resolution + launch command
    └── gui.py                # Tkinter window
```
