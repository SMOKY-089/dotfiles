#!/usr/bin/env bash

# Get internal display info (eDP-*)
OUTPUT_INFO=$(niri msg -j outputs | jq -r 'to_entries[] | select(.value.name | startswith("eDP")) | "\(.key) \(.value.modes[.value.current_mode].refresh_rate)"' | head -n 1)

if [ -z "$OUTPUT_INFO" ]; then
    OUTPUT_INFO=$(niri msg -j outputs | jq -r 'to_entries[0] | "\(.key) \(.value.modes[.value.current_mode].refresh_rate)"')
fi

OUTPUT_NAME=$(echo "$OUTPUT_INFO" | awk '{print $1}')
CURRENT_RATE=$(echo "$OUTPUT_INFO" | awk '{print $2}')

if [ "$CURRENT_RATE" -gt 100000 ]; then
    niri msg output "$OUTPUT_NAME" mode 1920x1080@60.019
    notify-send -t 1500 -a "Display" "Refresh Rate: 60Hz 🔋" "Switched to 60Hz battery saver"
else
    niri msg output "$OUTPUT_NAME" mode 1920x1080@144.003
    notify-send -t 1500 -a "Display" "Refresh Rate: 144Hz ⚡" "Switched to 144Hz smooth display"
fi
