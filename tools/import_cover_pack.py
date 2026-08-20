#!/usr/bin/env python3
"""Import a fan-made cover-art pack into the launcher's images/ folder.

Matches pack images to games by base title (the game name with trailing
parenthetical tags like "(Europe)" or catalog numbers like "(15871)"
stripped), since art packs are usually named by region/variant while a
scanned ROM collection is often catalogued by numeric ID instead. One
matched image is applied to every game sharing that base title. Existing
`<title>-image.png` / `<title>-thumb.png` files are never overwritten —
this only fills in games that have no art yet.

Usage:
    python3 tools/import_cover_pack.py <pack_dir> <games_dir> [--subset NAME]... [--apply]

Without --apply, it only reports what would be copied (dry run).
--subset can be passed multiple times to control which subfolders of the
pack are used and in what priority order (later subsets override earlier
ones for the same base title). Defaults to the Lassiveran pack's layout.
"""
import argparse
import os
import re
import shutil
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from launcher import scanner  # noqa: E402

DEFAULT_SUBSETS = ["BOX COVERS (#-Z)", "TEXT ADVENTURE SUBSET", "MAGAZINE SUBSET"]
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg"}


def base_title(title):
    return re.sub(r"(\s*\([^)]*\))+\s*$", "", title).strip().lower()


def build_pack_index(pack_dir, subsets):
    """base title -> source image path, later subsets win on collision."""
    index = {}
    for subset in subsets:
        subset_dir = os.path.join(pack_dir, subset)
        if not os.path.isdir(subset_dir):
            print(f"warning: subset folder not found, skipping: {subset_dir}")
            continue
        for name in os.listdir(subset_dir):
            ext = os.path.splitext(name)[1].lower()
            if ext not in IMAGE_EXTENSIONS:
                continue
            index[base_title(os.path.splitext(name)[0])] = os.path.join(subset_dir, name)
    return index


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pack_dir", help="Folder containing the extracted art pack")
    parser.add_argument("games_dir", help="Games folder (same one configured in the launcher)")
    parser.add_argument(
        "--subset", action="append", dest="subsets",
        help="Subfolder to pull from, in priority order (repeatable). Defaults to the Lassiveran pack layout.",
    )
    parser.add_argument("--apply", action="store_true", help="Actually copy files (default is dry run)")
    args = parser.parse_args()

    subsets = args.subsets or DEFAULT_SUBSETS
    pack_index = build_pack_index(args.pack_dir, subsets)
    print(f"Indexed {len(pack_index)} base titles from the pack.")

    games = scanner.scan_games(args.games_dir)
    games_by_base = {}
    for g in games:
        games_by_base.setdefault(base_title(g["title"]), []).append(g["title"])

    images_dir = os.path.join(args.games_dir, "images")
    os.makedirs(images_dir, exist_ok=True)
    existing = set(os.listdir(images_dir))

    copied, skipped = 0, 0
    for base, src in pack_index.items():
        for full_title in games_by_base.get(base, []):
            dest_name = f"{full_title}-image.png"
            if dest_name in existing or f"{full_title}-thumb.png" in existing:
                skipped += 1
                continue
            dest_path = os.path.join(images_dir, dest_name)
            if args.apply:
                shutil.copyfile(src, dest_path)
                existing.add(dest_name)
            copied += 1

    verb = "Copied" if args.apply else "Would copy"
    print(f"{verb}: {copied}")
    print(f"Skipped (already had art): {skipped}")
    if not args.apply:
        print("Dry run only -- pass --apply to actually copy files.")


if __name__ == "__main__":
    main()
