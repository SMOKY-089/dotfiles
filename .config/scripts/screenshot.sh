#!/usr/bin/env bash
mkdir -p ~/Pictures/Screenshots

TEMP_IMG=$(mktemp /tmp/screenshot_XXXXXX.png)
OUTPUT_IMG="$HOME/Pictures/Screenshots/Screenshot_$(date '+%Y%m%d_%H%M%S').png"

# Capture with latchshot:
# - Hover over a window to snap/latch to it
# - Click to capture the snapped window
# - Drag to select a custom region
# - Press 'f' for fullscreen capture
# - Press 'Escape' to cancel
if latchshot -o "$TEMP_IMG" --no-notify; then
    satty --filename "$TEMP_IMG" \
          --output-filename "$OUTPUT_IMG" \
          --copy-command wl-copy \
          --early-exit copy,save
    rm -f "$TEMP_IMG"
else
    rm -f "$TEMP_IMG"
fi
