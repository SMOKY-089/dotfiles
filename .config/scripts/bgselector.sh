#!/usr/bin/env bash
# Wallpick-backed Animated Wallpaper Carousel for Niri

COLLECTION_DIR="$HOME/.cache/wallpick/collection"
WALL_DIR="$HOME/Pictures/Wallpapers"

mkdir -p "$COLLECTION_DIR"

# Fast incremental hardlink sync for subdirectories (Catppuccin, Gruvbox, Nord, etc.)
python3 -c "
import os

target = os.path.expanduser('~/.cache/wallpick/collection')
root = os.path.expanduser('~/Pictures/Wallpapers')

try:
    existing = set(os.listdir(target))
except Exception:
    existing = set()

found = set()
for r, _, files in os.walk(root):
    if 'collection' in r or '.cache' in r:
        continue
    for f in files:
        if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp', '.gif')):
            full = os.path.join(r, f)
            rel = os.path.relpath(full, root)
            clean = rel.replace('/', ' • ')
            found.add(clean)
            if clean not in existing:
                try:
                    os.link(full, os.path.join(target, clean))
                except Exception:
                    pass

for old in existing - found:
    try:
        os.remove(os.path.join(target, old))
    except Exception:
        pass
" &

exec wallpick