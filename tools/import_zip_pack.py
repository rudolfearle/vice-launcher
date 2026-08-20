#!/usr/bin/env python3
"""Import cover-art images bundled in zip files into the launcher's images/ folder.

Unlike import_cover_pack.py (which expects an already-extracted pack with
named subset folders), this reads images directly out of one or more .zip
files in a folder -- e.g. a set of "C64 Logos (A-Z).zip" archives -- without
extracting them all to disk first.

Matching is base-title (region/catalog-number tags stripped) with a
normalization pass (lowercase, "&" -> "and", punctuation stripped), since
these packs are usually named "007 Car Chase.png" while the ROM collection
might have "007 Car Chase (9892).zip". Titles that don't match exactly after
normalization fall back to fuzzy matching (rapidfuzz token_sort_ratio) so
things like "The Hammer of Grimmold" vs "Hammer of Grimmold, The" or
"Elektraglide" vs "Elektra Glide" still match. A high score cutoff (90 by
default) keeps that fallback from pairing unrelated games (e.g. "Skate" vs
"Skat", a card game).

Usage:
    python3 tools/import_zip_pack.py <pack_dir> <games_dir> [--apply] [--fuzzy-cutoff N]

Without --apply, only reports what would be copied (dry run). Existing
<title>-image.png / <title>-thumb.png files are never overwritten.
"""
import argparse
import os
import re
import shutil
import sys
import zipfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from launcher import scanner  # noqa: E402

IMAGE_EXTENSIONS = {".png", ".gif", ".jpg", ".jpeg"}
JUNK_PATTERNS = [re.compile(r"^cooltext\d+$")]
JUNK_MAX_LEN = 60


def normalize(title):
    s = title.lower().replace("&", " and ")
    s = re.sub(r"[^a-z0-9 ]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def base_title(title):
    return re.sub(r"(\s*\([^)]*\))+\s*$", "", title).strip()


def is_junk(normalized_title):
    if len(normalized_title) > JUNK_MAX_LEN:
        return True
    return any(p.match(normalized_title) for p in JUNK_PATTERNS)


def build_pack_index(pack_dir):
    """normalized title -> (zip_path, member_name)."""
    index = {}
    for fname in sorted(os.listdir(pack_dir)):
        if not fname.lower().endswith(".zip"):
            continue
        zip_path = os.path.join(pack_dir, fname)
        with zipfile.ZipFile(zip_path) as zf:
            for member in zf.namelist():
                if member.endswith("/"):
                    continue
                ext = os.path.splitext(member)[1].lower()
                if ext not in IMAGE_EXTENSIONS:
                    continue
                title = os.path.splitext(os.path.basename(member))[0]
                norm = normalize(title)
                if norm and not is_junk(norm):
                    index[norm] = (zip_path, member)
    return index


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pack_dir", help="Folder containing the .zip art pack files")
    parser.add_argument("games_dir", help="Games folder (same one configured in the launcher)")
    parser.add_argument("--apply", action="store_true", help="Actually copy files (default is dry run)")
    parser.add_argument(
        "--fuzzy-cutoff", type=float, default=90.0,
        help="Minimum rapidfuzz token_sort_ratio score (0-100) to accept a fuzzy match (default: 90)",
    )
    parser.add_argument(
        "--no-fuzzy", action="store_true", help="Only use exact normalized-title matches"
    )
    args = parser.parse_args()

    pack_index = build_pack_index(args.pack_dir)
    print(f"Indexed {len(pack_index)} images across zips in {args.pack_dir}")

    games = scanner.scan_games(args.games_dir)
    games_by_base = {}
    for g in games:
        norm = normalize(base_title(g["title"]))
        games_by_base.setdefault(norm, []).append(g["title"])

    images_dir = os.path.join(args.games_dir, "images")
    os.makedirs(images_dir, exist_ok=True)
    existing = set(os.listdir(images_dir))

    exact_matches = {}   # normalized pack title -> normalized game base (itself)
    fuzzy_matches = {}   # normalized pack title -> normalized game base

    for norm_title in pack_index:
        if norm_title in games_by_base:
            exact_matches[norm_title] = norm_title

    if not args.no_fuzzy:
        from rapidfuzz import process, fuzz

        candidates = list(games_by_base.keys())
        unmatched = [t for t in pack_index if t not in exact_matches]
        for norm_title in unmatched:
            match = process.extractOne(
                norm_title, candidates, scorer=fuzz.token_sort_ratio,
                score_cutoff=args.fuzzy_cutoff,
            )
            if match:
                fuzzy_matches[norm_title] = match[0]

    copied, skipped = 0, 0
    fuzzy_applied = []
    for norm_title, (zip_path, member) in pack_index.items():
        game_base = exact_matches.get(norm_title) or fuzzy_matches.get(norm_title)
        if game_base is None:
            continue
        is_fuzzy = norm_title in fuzzy_matches
        for full_title in games_by_base[game_base]:
            dest_name = f"{full_title}-image.png"
            if dest_name in existing or f"{full_title}-thumb.png" in existing:
                skipped += 1
                continue
            dest_path = os.path.join(images_dir, dest_name)
            if args.apply:
                with zipfile.ZipFile(zip_path) as zf, zf.open(member) as src, open(dest_path, "wb") as dst:
                    shutil.copyfileobj(src, dst)
                existing.add(dest_name)
            copied += 1
            if is_fuzzy:
                fuzzy_applied.append((norm_title, game_base, full_title))

    verb = "Copied" if args.apply else "Would copy"
    print(f"Exact matches: {len(exact_matches)}")
    print(f"Fuzzy matches: {len(fuzzy_matches)} (cutoff={args.fuzzy_cutoff})")
    print(f"{verb}: {copied}")
    print(f"Skipped (already had art): {skipped}")

    if fuzzy_applied:
        print(f"\nFuzzy matches used ({len(fuzzy_applied)} game entries) -- spot-check these:")
        for pack_title, game_base, full_title in sorted(fuzzy_applied, key=lambda x: x[2]):
            print(f"  {pack_title!r} -> {full_title!r}")

    if not args.apply:
        print("\nDry run only -- pass --apply to actually copy files.")


if __name__ == "__main__":
    main()
