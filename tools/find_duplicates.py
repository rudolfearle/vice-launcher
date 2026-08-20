#!/usr/bin/env python3
"""Flag likely-duplicate games (same game, different release/naming) for
manual review.

Groups games by a normalized key: trailing parenthetical tags stripped
(region, catalog number, version) and a trailing roman numeral converted to
its arabic form (so "Game II" and "Game 2" group together). This catches
things like:

    Turrican (USA).zip  vs  Turrican (Europe).zip
    Bomb Jack 2.zip      vs  Bomb Jack II.zip

Nothing is deleted. For each group with more than one member, one file is
picked as "kept" (left alone) and the rest are copied -- not moved -- into
<games_dir>/dublicates/ for you to review and delete by hand if you agree
they're really the same game. A manifest (duplicate_report.txt) is written
there explaining each grouping.

Usage:
    python3 tools/find_duplicates.py <games_dir> [--apply]

Without --apply, only reports what would be grouped/copied (dry run).
"""
import argparse
import os
import re
import shutil
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from launcher import scanner  # noqa: E402

ROMAN_TO_ARABIC = {
    "I": "1", "II": "2", "III": "3", "IV": "4", "V": "5",
    "VI": "6", "VII": "7", "VIII": "8", "IX": "9", "X": "10",
    "XI": "11", "XII": "12", "XIII": "13", "XIV": "14", "XV": "15",
    "XVI": "16", "XVII": "17", "XVIII": "18", "XIX": "19", "XX": "20",
}

DUPLICATES_DIRNAME = "dublicates"


def base_title(title):
    return re.sub(r"(\s*\([^)]*\))+\s*$", "", title).strip()


def normalize_trailing_numeral(title):
    words = title.split(" ")
    if not words:
        return title
    last = words[-1].upper().rstrip(".")
    if last in ROMAN_TO_ARABIC:
        words[-1] = ROMAN_TO_ARABIC[last]
        return " ".join(words)
    return title


def duplicate_key(title):
    return normalize_trailing_numeral(base_title(title)).strip().lower()


def has_descriptive_tag(title):
    """True if title's trailing parenthetical tag has letters in it (e.g.
    "(USA)", "(Europe) (Alt)") rather than being just a bare catalog number
    like "(9892)". A bare-number-only match is too weak a signal on its own
    -- many unrelated indie/homebrew games share a generic title (Othello,
    Hangman, Labyrinth, ...) and are only told apart by that catalog ID, so
    treating all of them as "the same game, different release" would be
    wrong more often than not.
    """
    tags = re.findall(r"\(([^)]*)\)", title)
    return any(re.search(r"[A-Za-z]", tag) for tag in tags)


def is_reliable_group(members):
    raw_bases = {base_title(g["title"]) for g in members}
    if len(raw_bases) > 1:
        # Members only share a key after roman-numeral normalization
        # (e.g. "Game 2" / "Game II") -- that's a strong signal on its own.
        return True
    # All members share the same literal base title -- only trust it if at
    # least one has an actual region/version tag, not just a bare catalog ID.
    return any(has_descriptive_tag(g["title"]) for g in members)


def unique_dest_path(dest_dir, filename):
    candidate = os.path.join(dest_dir, filename)
    if not os.path.exists(candidate):
        return candidate
    stem, ext = os.path.splitext(filename)
    n = 2
    while True:
        candidate = os.path.join(dest_dir, f"{stem} ({n}){ext}")
        if not os.path.exists(candidate):
            return candidate
        n += 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("games_dir", help="Games folder (same one configured in the launcher)")
    parser.add_argument("--apply", action="store_true", help="Actually copy files (default is dry run)")
    args = parser.parse_args()

    games = scanner.scan_games(args.games_dir)
    print(f"Scanned {len(games)} games.")

    groups = {}
    for g in games:
        groups.setdefault(duplicate_key(g["title"]), []).append(g)

    candidate_groups = {k: v for k, v in groups.items() if len(v) > 1}
    dup_groups = {k: v for k, v in candidate_groups.items() if is_reliable_group(v)}
    skipped_low_confidence = len(candidate_groups) - len(dup_groups)
    total_dupes = sum(len(v) - 1 for v in dup_groups.values())
    print(f"Duplicate groups: {len(dup_groups)}")
    print(f"Skipped (same bare title, no region/version tag -- too ambiguous): {skipped_low_confidence} groups")
    print(f"Files that would be copied for review: {total_dupes}")

    dest_dir = os.path.join(args.games_dir, DUPLICATES_DIRNAME)
    if args.apply:
        os.makedirs(dest_dir, exist_ok=True)

    manifest_lines = []
    copied = 0
    for key, members in sorted(dup_groups.items()):
        members = sorted(members, key=lambda g: g["path"])
        kept = members[0]
        manifest_lines.append(f"\nGroup: {key!r}")
        manifest_lines.append(f"  KEPT (left in place): {kept['path']}")
        for dup in members[1:]:
            manifest_lines.append(f"  DUPLICATE (copied for review): {dup['path']}")
            if args.apply:
                dest = unique_dest_path(dest_dir, os.path.basename(dup["path"]))
                shutil.copy2(dup["path"], dest)
            copied += 1

    verb = "Copied" if args.apply else "Would copy"
    print(f"{verb}: {copied}")

    if args.apply:
        manifest_path = os.path.join(dest_dir, "duplicate_report.txt")
        with open(manifest_path, "w") as f:
            f.write(f"Duplicate review report -- {len(dup_groups)} groups, {copied} files copied\n")
            f.write("=" * 70 + "\n")
            f.write("\n".join(manifest_lines))
            f.write("\n")
        print(f"Manifest written to: {manifest_path}")
    else:
        print("\nSample groups:")
        for key, members in sorted(dup_groups.items())[:20]:
            titles = [g["title"] for g in sorted(members, key=lambda g: g["path"])]
            print(f"  {key!r}: {titles}")
        print("\nDry run only -- pass --apply to actually copy files.")


if __name__ == "__main__":
    main()
