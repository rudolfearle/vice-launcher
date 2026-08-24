# VICE Game Launcher — Progress & Next Steps

_Last updated: 2026-08-20_

## Status: Phases 1-3 complete, pushed to GitHub. Real VICE launch confirmed working.

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

## Process tracking / return-to-front — done (2026-08-20)

- [x] `_launch_selected` keeps the `Popen` handle from `vice.launch_game`
      and hands it to `_watch_process`, which polls `proc.poll()` via
      `self.after(500, ...)` (no extra thread needed — Tkinter-safe).
      When the process exits, the status bar updates
      (`"<title> exited. Ready."`) and the window is brought back with
      `deiconify()` / `lift()` / `focus_force()`.
- [x] Guards `self.winfo_exists()` before each poll so a closed window
      doesn't leave a dangling `after()` callback.

**Tested:** a scripted check that launches a short-lived fake process,
iconifies the window (simulating it being minimized while "playing"),
pumps the Tk event loop, and confirms the status bar and window state
both update correctly once the process exits.

## Packaging — done (2026-08-20)

- [x] `vice-launcher.spec` (PyInstaller onefile + windowed) and
      `tools/build_binary.sh` (creates a `.build-venv`, installs
      PyInstaller into it, builds via the spec) produce a standalone
      `dist/vice-launcher` binary (~12MB, no system Python required to
      run it).
- [x] **Packaging bug caught and fixed along the way:** `config.json`'s
      path was derived from `__file__`, which under a PyInstaller
      onefile build resolves into a temp extraction dir that's wiped
      after every run — settings would have silently reset on every
      launch of the packaged binary. Config now lives at
      `~/.config/vice-launcher/config.json` (respecting
      `$XDG_CONFIG_HOME`, overridable via `$VICE_LAUNCHER_CONFIG`), with
      a one-time automatic migration from the old project-root
      `config.json` for existing dev installs (frozen builds skip
      migration, since a distributed binary shouldn't assume access to
      a dev checkout's project root).

**Tested:** `py_compile`; verified migration copies an existing
project-root `config.json` (games_dir, joydev1, recent history) into the
new XDG path correctly; built the binary via `tools/build_binary.sh`
from a clean `build/`/`dist/`; ran the built binary standalone (no
crash, clean exit on timeout) and confirmed it reads the same XDG config
path as the dev-mode script.

## Phase 3 — all items complete

## Desktop launcher points at the packaged binary (2026-08-20)

`vice-launcher.desktop` (both the repo copy and `~/Desktop/`) now runs
`dist/vice-launcher` directly instead of `python3 main.py`. Since the
shortcut no longer runs from source, **the binary must be rebuilt after
any change to `launcher/*.py` or `main.py`** (`./tools/build_binary.sh`)
or the desktop icon will keep launching the old build. This is now a
standing rule (saved to session memory) — done automatically after
future source changes, no need to ask again.

## Cover art: fuzzy-matched zip pack import (2026-08-20)

- [x] Imported a second art source: a set of "C64 Logos (A-Z).zip"
      archives dropped in
      `/media/SHARE/roms/c64/images/images packs/`. Unlike the
      Lassiveran pack, these use plain titles with no region/version
      tags (e.g. `007 Car Chase.png`), so exact base-title matching
      already caught 2,972 of 3,422 images.
- [x] Added `tools/import_zip_pack.py` — reads images directly out of
      zip files (no full extraction needed), matches on a normalized
      base title (lowercase, `&`→`and`, punctuation stripped), and
      falls back to fuzzy matching (`rapidfuzz` `token_sort_ratio`,
      cutoff 90) for the remainder — mostly TOSEC `"X, The"` vs pack
      `"The X"` reordering and minor spelling variants (`Elektraglide`
      vs `Elektra Glide`). Filters obvious junk filenames
      (`cooltext123...` placeholder graphics). Every fuzzy match is
      printed for review; a lower cutoff (88) was tested first and
      rejected after it paired unrelated games (`Skate` → `Skat`,
      `Dragon's Eye` → `Dragon's Keep`) — 90 was the cleanest cutoff
      found by inspection.
- [x] Applied: 2,972 exact + 235 fuzzy-matched image groups → 1,566
      newly copied covers (rest were already covered by the Lassiveran
      import). Total coverage: **5,944 / 22,021 games (~27%)**, up from
      4,215.

**Tested:** dry run vs `--apply` counts cross-checked; manually
eyeballed every one of the 110 game entries that came from a fuzzy
match (printed in the tool's output) and confirmed each pairing is
correct before trusting the cutoff.

## Letter-range filter buttons — done (2026-08-20)

Row of buttons below the search box (`1-0,A / B / C / D / E / F / G / H-I
/ J-K / L-M / N-O / P-Q / R / S / T / U-Z`, wrapping across 2 rows) plus a
Reset button. Clicking a button filters to titles starting with that
letter/range (combines with the search box); clicking the active one
again toggles it off; Reset clears both the letter filter and search
text. Active button highlighted (sunken + blue background via plain
`tk.Button`, since ttk's "pressed" state doesn't render distinctly
across themes). Note: user's requested list skipped "D" between C and
E -- included it anyway to keep full A-Z coverage, no gap.

**Tested:** unit checks on the matcher for every group including edge
cases (leading digit/symbol/apostrophe titles falling into "1-0,A"), a
scripted GUI check confirming click/toggle/reset/combine-with-search
all update `filtered_games` correctly and the active button's
background changes, and a visual screenshot confirming the layout.

## Duplicate game de-duplication — done (2026-08-20/21)

- [x] `scanner.scan_games` now de-duplicates by exact title (same title
      found in more than one subfolder -- e.g. `c64 tapes` duplicating a
      disk image already under a letter folder -- keeps only the first
      one found; directory traversal is sorted for reproducible
      results). Also excludes `images/` from scanning (cover-art zip
      packs dropped there were being picked up as 17 fake "games").
      Library went from 22,021 entries to 20,347 unique real games.
- [x] User reorganized the library: moved `bios/` out to
      `/media/SHARE/bios/biosC64` and created an empty `dublicates/`
      review folder under `roms/c64`. `scanner.py` now excludes both
      `dublicates` and `duplicates` (either spelling) from scans.
- [x] Added `tools/find_duplicates.py` for a broader class of
      duplicates the exact-title dedup above can't catch: same game
      under a different release naming convention -- region tags
      (`Turrican (USA)` vs `Turrican (Europe)`) or roman-numeral vs
      arabic sequel notation (`Bomb Jack 2` vs `Bomb Jack II`). Nothing
      is deleted -- one file per group is picked as "kept" (left alone)
      and the rest are *copied* into `dublicates/` for manual review,
      with a `duplicate_report.txt` manifest explaining every grouping.
      **Precision safeguard:** a group is only trusted if it has a real
      distinguishing signal (an actual region/version tag, or a
      roman-numeral difference) -- titles that differ *only* by a bare
      catalog number are skipped, since many unrelated indie/homebrew
      games share a generic name (Othello, Hangman, Mastermind, ...)
      and would otherwise get wrongly bundled as "the same game."
      Applied: 2,173 reliable groups, 3,006 files copied for review (921
      low-confidence groups skipped).

**Tested:** unit test on a mock folder tree (duplicate title, bios/,
images/ exclusion); dry run vs `--apply` counts cross-checked on the
real library; specifically re-verified that Othello/Hangman/Mastermind
(21/13/13 same-title entries, no real distinguishing tag) are correctly
excluded while genuine variant families (10th Frame, 1942, 3D Stock Cars
II/2, ...) are correctly grouped.

## Cover art: ScreenScraper / TheGamesDB downloader — built, pending credentials (2026-08-21)

Investigated Batocera's three image sources (ScreenScraper, TheGamesDB,
Arcade Database) for filling the remaining ~71% of games with no cover
art. **Arcade Database ruled out** -- it's MAME's own database; its
"Commodore 64" entries are for MAME emulating the C64 as a system
(softlist ROMs), not a general TOSEC-style box-art source, so it
wouldn't have meaningful coverage here. Built `tools/download_covers.py`
against ScreenScraper (`jeuInfos.php`, systemeid=66) and TheGamesDB
(`Games/ByGameName` + `Games/Images`, platform ID looked up dynamically
rather than hardcoded) -- both require the user's own registered API
credentials (free, but registration can't be done on their behalf).
Downloaded images are converted to real PNG via Pillow (tool-time only,
not a runtime dependency of the packaged app) so format never matters.
Credentials read from a local gitignored JSON file
(`~/.config/vice-launcher/scraper_credentials.json`), never committed;
`tools/scraper_credentials.example.json` documents the shape.

**Tested:** dry run (no network calls) confirmed correct on the real
library (14,717 / 20,347 games missing art); refuses to proceed under
`--apply` with missing/incomplete credentials; both API clients'
response-parsing logic unit-tested against mocked HTTP responses
(including two conflicting TheGamesDB response shapes found during
research, both handled); PNG conversion verified end-to-end including
that `tk.PhotoImage` (what the real app uses) loads the result cleanly.
**Not yet tested: live API calls** -- pending the user registering for
ScreenScraper devid/devpassword + ssid/sspassword and a TheGamesDB API
key.

## Cover art downloader: live runs (2026-08-21 to 2026-08-24)

**TheGamesDB run:** credentials worked immediately (platform id 40
confirmed). Ran a 500-game batch -- but the tool had a real bug: it
silently treated a 429 (rate limited) the same as "not found," so once
the account's **monthly** quota hit 0 partway through (after 276 real
downloads), it spent the next hour grinding through the remaining
~14,000 games with zero chance of success instead of stopping. Fixed:
both clients now detect 418/429 and raise `RateLimitExceeded`, which the
main loop catches and stops on immediately, printing
`remaining_monthly_allowance` / refresh time when TheGamesDB provides
it (verified against the real, still-exhausted account -- refreshes in
~30 days from 2026-08-21).

**ScreenScraper run:** first devid/devpassword attempt got a 403
("Vérifier vos identifiants développeur") -- those came from a
different source than the account's own login; re-requested/corrected
via the forum and it started working. Also found (and fixed) that
ScreenScraper's media URLs embed devid/devpassword/ssid/sspassword as
plain query-string params -- `redact_credentials()` now strips these
out of any error message before it's printed or logged, so a network
error never leaks them into a log file. Account quota check
(`ssuser.requeststoday` / `maxrequestsperday`) showed massive headroom
(50,000/day; `requestskotoday` tracks *failed* requests specifically,
not general usage, so it isn't the binding constraint). Ran a small
300-game validation batch (clean, 0 errors), then the full remaining
backlog in one long background run (~10-15 hours, via `nohup` +
`Monitor` with `tail -f --pid=<pid>` so the watch ends automatically
when the process exits):

- Downloaded: 5,784
- Not found on ScreenScraper: 8,334
- Errors: 20 (one transient network blip -- "no route to host," self-
  recovered within minutes -- plus a handful of "cannot identify image
  file" for a few malformed responses)
- No rate limit hit at any point

**Coverage: 5,944 -> 11,993 / 20,347 games (58.9%)**, combining the
Lassiveran pack, the zip-logo pack, and now ScreenScraper/TheGamesDB.
TheGamesDB remains unavailable until its monthly quota resets
(~2026-09-20); re-running `download_covers.py --source thegamesdb`
after that (or `--source both` once ScreenScraper alone doesn't cover
enough) would pick up more of the remaining ~8,354 games with no art at
all.

## Decisions made so far (for reference)

- **GUI toolkit:** Tkinter, chosen for zero extra dependencies. PyQt6
  remains the upgrade path if a grid/cover-art view becomes a priority.
- **Default machine:** `x64sc` (accurate C64 core) for all supported
  extensions, since the large majority of ROMs in circulation are C64.
- **VICE discovery:** binary folder is configurable rather than assumed,
  to handle the apt vs RPM Fusion vs Flatpak install differences between
  Mint and Fedora.
