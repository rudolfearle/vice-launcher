# VICE Game Launcher — Progress & Next Steps

_Last updated: 2026-08-20_

## Status: Phase 1 and Phase 2 complete, pushed to GitHub. Real VICE launch confirmed working.

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

Real-world launch against actual VICE and a real game library is now
confirmed working — see "Real-world launch test" below.

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
errors.

## Real-world launch test — passed (2026-08-20)

Ran the full launch path against the real library at
`/media/SHARE/roms/c64` (22,021 games, almost entirely `.zip`) with the
actual `x64sc` binary (VICE 3.7.1, apt-installed):

- Scanned the library successfully (22,021 entries).
- Picked a zipped game (`b/Boulder Dash 12 (15871).zip`), containing a
  `.T64` tape image.
- The zip auto-extract fallback correctly pulled `BDASH12.T64` out to a
  temp dir and launched that instead of the raw zip.
- `x64sc -autostart <extracted .T64>` ran to completion: loaded the C64
  ROMs, attached the tape image, autostarted the program, and the
  process stayed alive (confirmed via `Popen.poll()` after 5s, then
  cleanly terminated by us).

**Blocker hit and resolved along the way:** the apt `vice` package
ships with no C64 ROMs (kernal/basic/chargen are copyrighted and
excluded per `/usr/share/doc/vice/README.ROMs`). VICE failed with
`Couldn't load kernal ROM` until ROMs were supplied. This is a
machine-setup issue, not a launcher bug. Fix used on this machine:
copied `kernal-901227-03.bin`, `basic-901226-01.bin`, and
`chargen-901225-01.bin` into the per-user ROM path
`~/.local/share/vice/C64/` (no root needed — this path is checked
before the system-wide `/usr/share/vice/C64/`). Note VICE 3.7.1's
compiled-in default expects those exact revisioned filenames, not the
generic `kernal`/`basic`/`chargen` names some older docs reference.
This ROM setup lives outside the repo (per-user, not project state) —
nothing to commit for it.

**Local config:** `config.json` (gitignored) now has `games_dir` set to
`/media/SHARE/roms/c64` on this machine so the app opens straight into
the real library. Also cleared out some stale test data (`recent`
entries like `/games/g24.d64`) that had leaked into it from an earlier
unit test run that didn't scope its `CONFIG_PATH` to a scratch file.

## Cover art preview — done (2026-08-20)

- [x] Split the main window into a game list (left) and an image preview
      panel (right, ~280px). Selecting a game (click, arrow keys) updates
      the preview via `<<ListboxSelect>>`.
- [x] `launcher/covers.py: find_cover_path` looks for
      `<games_dir>/images/<title>-image.png`, falling back to
      `<title>-thumb.png`, matching art dropped in
      `/media/SHARE/roms/c64/images` (1,444 files covering ~722 of the
      22,004 games — most titles simply have no art, and that's expected
      given the dataset, not a matching bug).
- [x] Images are loaded with plain `tk.PhotoImage` (no Pillow dependency)
      and downscaled to fit a 260x300 box via integer `subsample()`.
      Falls back to a "No image available" label when there's no match
      or the file fails to load.

**Tested:** `py_compile`, a scripted check that builds `LauncherApp`,
confirms the preview panel sits to the right of the list via widget
geometry, and confirms selecting a game with known art
(`1942 (15)`) attaches a correctly-resized image (224x256) to the
preview label.

## Joystick/controller configuration — done (2026-08-20)

- [x] `launcher/joystick.py: detect_analog_joysticks` scans `/dev/input/js*`
      and reads the device name from `/sys/class/input/jsN/device/name`,
      with a fallback decoder for pads that report a mis-encoded (looks
      like UTF-16-in-UTF-8) name string — the Astrum PS2-lookalike
      connected on this machine (Sony DualShock3 VID/PID `054c:0268`,
      handled by the kernel's `hid-sony` driver) hit exactly this case.
- [x] Preferences dialog gained "Joystick port 1" / "Joystick port 2"
      dropdowns listing None/Numpad/Keyset 1/Keyset 2 plus any detected
      analog joysticks by name. Persisted in `config.json` as `joydev1`
      / `joydev2` (VICE's own `-joydevN` device codes).
- [x] `vice.py: JOYSTICK_PORTS` maps which native joystick ports each
      machine binary actually supports (PET and CBM-II have none, VIC-20
      has one, C64/C128/Plus4 have two) so `launch_game` only appends
      `-joydev1`/`-joydev2` when the target machine supports that port —
      passing an unsupported flag makes those VICE binaries error out.

**Tested:** `py_compile`, unit checks confirming the built launch command
includes both joydev flags for x64sc, only `-joydev1` for xvic, and
neither for xpet, a scripted Preferences-dialog check that saving a
selected joystick label round-trips to the correct device code in
`cfg["joydev1"]`, and a real launch against the actual connected
controller — VICE's log confirmed
`registered controller '...PLAYSTATION(R)3 Controller' with 6 axes, 0
hats, 17 buttons` and the game autostarted normally with
`-joydev1 4 -joydev2 0` on the command line.

## Next steps

## Phase 3 (polish)

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
