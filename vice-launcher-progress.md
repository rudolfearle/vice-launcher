# VICE Game Launcher — Progress & Next Steps

_Last updated: 2026-08-20_

## Status: Phase 1 and Phase 2 complete, pushed to GitHub

Repo: https://github.com/rudolfearle/vice-launcher

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

## Phase 2 — done

- [x] Favorites list — right-click a game to add/remove; View menu has an
      "All Games" / "Favorites" / "Recently Played" toggle. Persisted in
      `config.json` under `favorites` (list of paths).
- [x] "Recently played" tracking — recorded on every successful launch,
      newest first, capped at 20 entries (`config.py: RECENT_LIMIT`).
      Persisted under `recent` (list of `{path, ts}`).
- [x] Per-game machine override — right-click > Set Machine, checkmark
      shows the active choice (including "Default"). Persisted under
      `machine_overrides` (`{path: machine}`) in `config.json`.
- [x] Zip auto-extract fallback — `vice.py: _extract_zip_entry` unzips the
      first supported image found inside a `.zip` to a temp dir and
      launches that directly; falls back to launching the zip as-is only
      if nothing usable is found inside (bad zip, no supported member).
- [x] Settings dialog — File > Preferences opens a proper `Toplevel`
      (games folder, VICE binary folder, Flatpak toggle, default machine
      dropdown) instead of raw folder-picker menu items.

**Tested:** `py_compile` on all modules, unit-style checks of the new
`config.py` helpers (favorites toggle, recent-list capping/ordering,
machine override get/set) and the zip extraction fallback (both a zip
with a usable image and one without), plus a scripted Tk smoke test that
builds `LauncherApp`, loads a fake library, exercises the favorites view,
sets a machine override, and opens `PreferencesDialog` — all without
errors. Still not tested: an actual VICE binary launching a real game.

## Next steps

## Phase 3 (polish)

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
