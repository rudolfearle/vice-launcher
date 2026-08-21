#!/usr/bin/env python3
"""Download missing box art from ScreenScraper and/or TheGamesDB into the
launcher's images/ folder.

Only fills gaps -- games that already have a `<title>-image.png` or
`<title>-thumb.png` (from a manual import or a prior run of this tool) are
skipped. Tries ScreenScraper first (generally the best C64 box-art
coverage), then falls back to TheGamesDB if nothing was found there.

Credentials are never read from the command line or hardcoded -- they live
in a local JSON file next to the launcher's config.json
(~/.config/vice-launcher/scraper_credentials.json by default, overridable
via --credentials), which is your own file and is never committed to git.
See scraper_credentials.example.json in this folder for the expected shape.

Registration (you have to do this yourself -- these are personal API keys):
  ScreenScraper: create an account at https://www.screenscraper.fr/, then
    request devid/devpassword via their forum:
    https://www.screenscraper.fr/forumsujets.php?frub=12
  TheGamesDB: create an account at https://thegamesdb.net/, then request an
    API key at https://api.thegamesdb.net/key.php

Usage:
    python3 tools/download_covers.py <games_dir> [--apply] [--source screenscraper|thegamesdb|both]
                                      [--limit N] [--credentials PATH]

Without --apply, only reports how many games are missing art and would be
queried -- no network calls are made.
"""
import argparse
import io
import json
import os
import re
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from launcher import config as cfgmod  # noqa: E402
from launcher import covers, scanner  # noqa: E402

SCREENSCRAPER_SYSTEM_ID = 66  # Commodore 64
SCREENSCRAPER_BASE = "https://www.screenscraper.fr/api2"
THEGAMESDB_BASE = "https://api.thegamesdb.net/v1"
REQUEST_DELAY_SECONDS = 1.5  # be polite -- both services rate-limit free accounts

DEFAULT_CREDENTIALS_PATH = os.path.join(
    os.path.dirname(cfgmod.CONFIG_PATH), "scraper_credentials.json"
)


class RateLimitExceeded(Exception):
    """Raised when a source reports its request quota is exhausted, so the
    caller can stop immediately instead of grinding through the rest of the
    (now-guaranteed-to-fail) list."""


def base_title(title):
    return re.sub(r"(\s*\([^)]*\))+\s*$", "", title).strip()


_CREDENTIAL_PARAMS = ("devid", "devpassword", "ssid", "sspassword", "apikey")


def redact_credentials(text):
    """Strip credential values out of a string (e.g. an exception message
    that embedded a request URL) before it's ever printed or logged --
    ScreenScraper's media URLs in particular carry devid/devpassword/ssid/
    sspassword as plain query params."""
    text = str(text)
    for param in _CREDENTIAL_PARAMS:
        text = re.sub(rf"({param}=)[^&\s]+", r"\1<redacted>", text, flags=re.IGNORECASE)
    return text


def load_credentials(path):
    if not os.path.exists(path):
        return {}
    with open(path) as f:
        return json.load(f)


def save_png(image_bytes, dest_path):
    from PIL import Image

    img = Image.open(io.BytesIO(image_bytes))
    img.convert("RGBA").save(dest_path, "PNG")


class ScreenScraperClient:
    def __init__(self, creds):
        self.ssid = creds.get("ssid", "")
        self.sspassword = creds.get("sspassword", "")
        self.devid = creds.get("devid", "")
        self.devpassword = creds.get("devpassword", "")

    def available(self):
        return bool(self.devid and self.devpassword)

    def find_box_art_url(self, title):
        import requests

        params = {
            "devid": self.devid,
            "devpassword": self.devpassword,
            "softname": "vice-launcher",
            "output": "json",
            "ssid": self.ssid,
            "sspassword": self.sspassword,
            "systemeid": SCREENSCRAPER_SYSTEM_ID,
            "romnom": base_title(title),
        }
        resp = requests.get(f"{SCREENSCRAPER_BASE}/jeuInfos.php", params=params, timeout=15)
        if resp.status_code in (418, 429):
            raise RateLimitExceeded(f"ScreenScraper returned {resp.status_code}: {resp.text[:200]}")
        if resp.status_code != 200:
            return None
        try:
            data = resp.json()
        except ValueError:
            return None
        jeu = data.get("response", {}).get("jeu")
        if not jeu:
            return None
        medias = jeu.get("medias", [])
        for wanted_type in ("box-2D", "box-3D"):
            for media in medias:
                if media.get("type") == wanted_type and media.get("url"):
                    return media["url"]
        return None


def _raise_if_rate_limited(resp, source_name):
    if resp.status_code not in (418, 429):
        return
    detail = ""
    try:
        body = resp.json()
        remaining = body.get("remaining_monthly_allowance")
        refresh_secs = body.get("allowance_refresh_timer")
        if remaining is not None:
            detail = f" (remaining_monthly_allowance={remaining}"
            if refresh_secs:
                detail += f", refreshes in {refresh_secs / 86400:.1f} days"
            detail += ")"
    except ValueError:
        pass
    raise RateLimitExceeded(f"{source_name} returned {resp.status_code}{detail}")


class TheGamesDBClient:
    def __init__(self, creds):
        self.api_key = creds.get("api_key", "")
        self._platform_id = None

    def available(self):
        return bool(self.api_key)

    def _c64_platform_id(self):
        import requests

        if self._platform_id is not None:
            return self._platform_id
        resp = requests.get(
            f"{THEGAMESDB_BASE}/Platforms", params={"apikey": self.api_key}, timeout=15
        )
        _raise_if_rate_limited(resp, "TheGamesDB")
        resp.raise_for_status()
        platforms = resp.json()["data"]["platforms"]
        for pid, info in platforms.items():
            if info.get("name", "").strip().lower() == "commodore 64":
                self._platform_id = int(pid)
                return self._platform_id
        raise RuntimeError("Could not find 'Commodore 64' in TheGamesDB platform list")

    def find_box_art_url(self, title):
        import requests

        platform_id = self._c64_platform_id()
        search = requests.get(
            f"{THEGAMESDB_BASE}/Games/ByGameName",
            params={
                "apikey": self.api_key,
                "name": base_title(title),
                "filter[platform][0]": platform_id,
            },
            timeout=15,
        )
        _raise_if_rate_limited(search, "TheGamesDB")
        if search.status_code != 200:
            return None
        games = search.json().get("data", {}).get("games", [])
        if not games:
            return None
        game_id = games[0]["id"]

        images = requests.get(
            f"{THEGAMESDB_BASE}/Games/Images",
            params={"apikey": self.api_key, "games_id": game_id, "filter[type]": "boxart"},
            timeout=15,
        )
        _raise_if_rate_limited(images, "TheGamesDB")
        if images.status_code != 200:
            return None
        payload = images.json().get("data", {})

        # TheGamesDB's documented response shape has shifted between API
        # versions in examples found during research; handle both so this
        # keeps working whichever one the live API actually returns.
        raw_base = payload.get("base_url")
        base_url_str = raw_base.get("original") if isinstance(raw_base, dict) else raw_base

        # Shape A: {"images": {"<game_id>": [{"type", "side", "filename"}, ...]}}
        entries = payload.get("images", {}).get(str(game_id), [])
        if entries and base_url_str:
            for want_side in ("front", None):
                for entry in entries:
                    if entry.get("type") == "boxart" and entry.get("filename") and (
                        want_side is None or entry.get("side") == want_side
                    ):
                        return f"{base_url_str}{entry['filename']}"

        # Shape B: {"boxart": {"front": {"url": "boxart/front/121-1.jpg"}, "back": {...}}}
        boxart = payload.get("boxart")
        if isinstance(boxart, dict) and base_url_str:
            front = boxart.get("front") or boxart.get("back")
            if isinstance(front, dict) and front.get("url"):
                return f"{base_url_str}{front['url']}"

        return None


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("games_dir", help="Games folder (same one configured in the launcher)")
    parser.add_argument("--apply", action="store_true", help="Actually query APIs and download (default is dry run)")
    parser.add_argument(
        "--source", choices=["screenscraper", "thegamesdb", "both"], default="both",
        help="Which service(s) to use (default: both, ScreenScraper first)",
    )
    parser.add_argument("--limit", type=int, default=None, help="Stop after this many successful downloads")
    parser.add_argument("--credentials", default=DEFAULT_CREDENTIALS_PATH, help="Path to credentials JSON file")
    args = parser.parse_args()

    creds = load_credentials(args.credentials)
    ss_client = ScreenScraperClient(creds.get("screenscraper", {}))
    tgdb_client = TheGamesDBClient(creds.get("thegamesdb", {}))

    use_ss = args.source in ("screenscraper", "both")
    use_tgdb = args.source in ("thegamesdb", "both")

    if args.apply:
        if use_ss and not ss_client.available():
            print(f"ScreenScraper credentials missing/incomplete in {args.credentials}")
            use_ss = False
        if use_tgdb and not tgdb_client.available():
            print(f"TheGamesDB credentials missing/incomplete in {args.credentials}")
            use_tgdb = False
        if not use_ss and not use_tgdb:
            print("No usable credentials for the requested source(s). Nothing to do.")
            return

    games = scanner.scan_games(args.games_dir)
    images_dir = os.path.join(args.games_dir, "images")
    missing = [g for g in games if not covers.find_cover_path(args.games_dir, g["title"])]
    print(f"Games missing cover art: {len(missing)} / {len(games)}")

    if not args.apply:
        print(f"Would query: {'ScreenScraper' if use_ss else ''}"
              f"{' + ' if use_ss and use_tgdb else ''}"
              f"{'TheGamesDB' if use_tgdb else ''}")
        print("\nDry run only -- pass --apply to actually query APIs and download images.")
        return

    os.makedirs(images_dir, exist_ok=True)
    downloaded, not_found, errors = 0, 0, 0
    stopped_early = None
    for g in missing:
        if args.limit is not None and downloaded >= args.limit:
            break
        title = g["title"]
        url = None
        try:
            if use_ss:
                url = ss_client.find_box_art_url(title)
            if url is None and use_tgdb:
                url = tgdb_client.find_box_art_url(title)
        except RateLimitExceeded as e:
            stopped_early = redact_credentials(e)
            break
        except Exception as e:
            print(f"  ERROR looking up {title!r}: {redact_credentials(e)}")
            errors += 1
            time.sleep(REQUEST_DELAY_SECONDS)
            continue

        if url is None:
            not_found += 1
            time.sleep(REQUEST_DELAY_SECONDS)
            continue

        try:
            import requests

            img_resp = requests.get(url, timeout=20)
            img_resp.raise_for_status()
            dest_path = os.path.join(images_dir, f"{title}-image.png")
            save_png(img_resp.content, dest_path)
            downloaded += 1
            print(f"  downloaded: {title}")
        except Exception as e:
            print(f"  ERROR downloading {title!r}: {redact_credentials(e)}")
            errors += 1

        time.sleep(REQUEST_DELAY_SECONDS)

    print(f"\nDownloaded: {downloaded}")
    print(f"Not found on any source: {not_found}")
    print(f"Errors: {errors}")
    if stopped_early:
        print(f"\nStopped early -- rate limit hit: {stopped_early}")


if __name__ == "__main__":
    main()
