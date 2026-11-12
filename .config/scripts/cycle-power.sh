#!/usr/bin/env bash
current=$(powerprofilesctl get)
if [ "$current" == "power-saver" ]; then
    powerprofilesctl set balanced
    notify-send -t 1500 -a "Power Profile" "Balanced Mode "
elif [ "$current" == "balanced" ]; then
    powerprofilesctl set performance
    notify-send -t 1500 -a "Power Profile" "Performance Mode "
else
    powerprofilesctl set power-saver
    notify-send -t 1500 -a "Power Profile" "Power Saver "
fi
