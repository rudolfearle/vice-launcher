import os

# Cover art lives in an "images" subfolder next to the games, named after
# the game title with one of these suffixes (full image preferred over thumb).
IMAGES_SUBDIR = "images"
IMAGE_SUFFIXES = ["-image.png", "-thumb.png"]


def find_cover_path(games_dir, title):
    if not games_dir:
        return None
    images_dir = os.path.join(games_dir, IMAGES_SUBDIR)
    if not os.path.isdir(images_dir):
        return None
    for suffix in IMAGE_SUFFIXES:
        candidate = os.path.join(images_dir, f"{title}{suffix}")
        if os.path.isfile(candidate):
            return candidate
    return None
