#!/usr/bin/env bash
if pgrep -x wlsunset > /dev/null; then
    killall wlsunset
    notify-send -t 1500 "Night Light" "Disabled ☀️"
else
    # 4500k color temp
    wlsunset -t 4500 &
    notify-send -t 1500 "Night Light" "Enabled 🌙"
fi
