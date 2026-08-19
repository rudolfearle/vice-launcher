# VICE Game Launcher — Progress & Next Steps

_Last updated: 2026-08-20_

## Status: Phase 1 complete (not yet on GitHub)

## What's done

A working Tkinter front-end for launching Commodore game images through
[VICE](https://vice-emu.sourceforge.io/). Runs locally with `python3 main.py`.

**Core features implemented:**
- Recursive folder scan for supported game files (`.d64`, `.d71`, `.d81`,
  `.g64`, `.t64`, `.tap`, `.prg`, `.p00`, `.crt`, `.zip`)
- Live search/filter box over the scanned library
- Launch via double-click, Enter, or a Launch button — shells out to
  `x64sc -autostart <file>`
- Settings persisted to `config.json`: games folder, VICE binary folder,
  and a Flatpak mode toggle (for `net.sf.VICE` installs)
- Graceful error handling when the VICE binary can't be found, instead
  of crashing

**Tested:**
- All modules compile cleanly (`py_compile`)
- Scanner correctly picks up supported extensions and ignores unrelated
  files (verified against a mock folder with `.d64`, `.crt`, and a
  `.txt` file)
- Machine-mapping and binary resolution logic verified, including the
  "VICE not installed" fallback path

**Not yet tested:** actually launching a real VICE binary against a real
game — the sandbox this was built in doesn't have VICE installed. Worth
doing as your first real-world check on Mint or Fedora.

## Project structure

```
vice-launcher/
├── config.json          # created on first save (gitignored — holds local paths)
├── main.py               # entry point
├── README.md              # setup + usage instructions
└── launcher/
    ├── config.py           # load/save settings
    ├── scanner.py            # recursive folder scan for game files
    ├── vice.py                 # binary resolution + launch command
    └── gui.py                    # Tkinter window
```

Delivered as `vice-launcher.zip`, git-initialized locally with one commit
("Phase 1: basic VICE game launcher"), `.gitignore` already excludes
`__pycache__` and `config.json`.

## Open item: push to GitHub

Not yet pushed — no GitHub connector is available to do this
automatically, and I don't hold your credentials. Two ways to finish it,
covered in detail earlier in this chat:

- **With `gh` CLI:** `gh repo create vice-launcher --public --source=. --remote=origin --push`
- **Without it:** create the repo on github.com, then `git remote add origin ... && git push -u origin main`

## Next steps — Phase 2 (quality of life)

- [ ] Favorites list (star a game, filter to favorites)
- [ ] "Recently played" tracking, persisted alongside config
- [ ] Per-game machine override in the UI (the mapping logic in
      `vice.py` already supports C128/VIC-20/Plus4/PET — just needs a
      dropdown/right-click menu exposed in `gui.py`)
- [ ] Handle `.zip` files that VICE can't open directly (auto-extract to
      a temp dir as a fallback)
- [ ] Basic settings dialog instead of raw folder pickers (e.g. a
      proper preferences window)

## Later — Phase 3 (polish)

- [ ] Cover art support — thumbnail per game, likely via a filename-keyed
      `covers/` folder
- [ ] Joystick/controller pass-through configuration
- [ ] Track the running VICE process so the launcher can detect when a
      game exits and bring itself back to front
- [ ] Packaging (PyInstaller) for a distributable binary, if wanted

## Decisions made so far (for reference)

- **GUI toolkit:** Tkinter, chosen for zero extra dependencies. PyQt6
  remains the upgrade path if a grid/cover-art view becomes a priority.
- **Default machine:** `x64sc` (accurate C64 core) for all supported
  extensions, since the large majority of ROMs in circulation are C64.
- **VICE discovery:** binary folder is configurable rather than assumed,
  to handle the apt vs RPM Fusion vs Flatpak install differences between
  Mint and Fedora.
