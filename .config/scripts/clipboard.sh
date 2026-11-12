#!/usr/bin/env bash
# Requires: cliphist, rofi-wayland
if [ "$1" == "store" ]; then
    wl-paste --type image --watch cliphist store &
    exec wl-paste --watch cliphist store
else
    cliphist list | rofi -dmenu -p "Clipboard" -display-columns 2 -theme-str "listview { lines: 10; }" | cliphist decode | wl-copy
fi
