#!/usr/bin/env python3
"""
Giant 24-Hour Military Desktop Clock Widget for Wayland / Niri
Uses GTK3 + GtkLayerShell to sit on the desktop backdrop with 100% input passthrough.
Default: Colossal Horizontal Military Clock ("2314" spanning >60% of the screen).
"""

import os
import sys
import time
import signal
import subprocess
import cairo
import gi

gi.require_version('Gtk', '3.0')
gi.require_version('GtkLayerShell', '0.1')
from gi.repository import Gtk, Gdk, GLib, GtkLayerShell

def kill_other_instances():
    current_pid = os.getpid()
    parent_pid = os.getppid()
    try:
        res = subprocess.run(["pgrep", "-f", "desktop-clock.py"], stdout=subprocess.PIPE, text=True, check=False)
        if res.returncode == 0:
            for line in res.stdout.strip().split():
                pid = int(line)
                if pid != current_pid and pid != parent_pid:
                    try:
                        os.kill(pid, signal.SIGTERM)
                    except ProcessLookupError:
                        pass
    except Exception:
        pass

class NothingClock(Gtk.Window):
    def __init__(self, stacked=False):
        super().__init__()
        self.stacked = stacked

        # Initialize as Wayland Layer Shell surface
        GtkLayerShell.init_for_window(self)
        GtkLayerShell.set_namespace(self, "desktop-clock")
        GtkLayerShell.set_layer(self, GtkLayerShell.Layer.BOTTOM)
        GtkLayerShell.set_exclusive_zone(self, -1)
        GtkLayerShell.set_keyboard_mode(self, GtkLayerShell.KeyboardMode.NONE)

        # Anchor to all four edges so it fills screen seamlessly
        for edge in [GtkLayerShell.Edge.TOP, GtkLayerShell.Edge.BOTTOM,
                     GtkLayerShell.Edge.LEFT, GtkLayerShell.Edge.RIGHT]:
            GtkLayerShell.set_anchor(self, edge, True)

        # Transparent RGBA visual
        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        if visual:
            self.set_visual(visual)

        # Center layout container
        self.box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.box.set_valign(Gtk.Align.CENTER)
        self.box.set_halign(Gtk.Align.CENTER)
        self.box.get_style_context().add_class("clock-container")

        if not self.stacked:
            # Default: Giant Horizontal Military style (e.g. "2314")
            self.single_label = Gtk.Label()
            self.single_label.get_style_context().add_class("clock-military")
            self.box.pack_start(self.single_label, False, False, 0)
        else:
            # Stacked Nothing OS style: HH over MM
            self.hours_label = Gtk.Label()
            self.hours_label.get_style_context().add_class("clock-digit")
            self.hours_label.get_style_context().add_class("hours")

            self.minutes_label = Gtk.Label()
            self.minutes_label.get_style_context().add_class("clock-digit")
            self.minutes_label.get_style_context().add_class("minutes")

            self.box.pack_start(self.hours_label, False, False, 0)
            self.box.pack_start(self.minutes_label, False, False, 0)

        self.add(self.box)

        # 100% Click-through: empty input shape means mouse passes right through
        self.connect("realize", self._on_realize)

        # Load Aesthetic CSS
        css_provider = Gtk.CssProvider()
        css = """
        window {
            background-color: transparent;
        }
        .clock-container {
            background-color: transparent;
            margin: 0;
            padding: 0;
        }
        .clock-military {
            font-family: 'Noto Sans', 'Inter', sans-serif;
            font-size: 450px;
            font-weight: 900;
            color: rgba(255, 255, 255, 0.88);
            letter-spacing: -18px;
            text-shadow: 0px 20px 64px rgba(0, 0, 0, 0.85);
            margin: 0;
            padding: 0;
        }
        .clock-digit {
            font-family: 'Noto Sans', 'Inter', sans-serif;
            font-size: 400px;
            font-weight: 900;
            color: rgba(255, 255, 255, 0.85);
            letter-spacing: -18px;
            text-shadow: 0px 16px 64px rgba(0, 0, 0, 0.75);
            margin: -55px 0;
            padding: 0;
        }
        """
        css_provider.load_from_data(css.encode())
        Gtk.StyleContext.add_provider_for_screen(
            screen,
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        self.update_time()
        GLib.timeout_add_seconds(1, self.update_time)

    def _on_realize(self, widget):
        # Apply 0x0 empty input region to pass all mouse events to wallpaper/windows
        window = self.get_window()
        if window:
            window.input_shape_combine_region(cairo.Region(), 0, 0)

    def update_time(self):
        now = time.localtime()
        if not self.stacked:
            self.single_label.set_text(time.strftime("%H%M", now))
        else:
            self.hours_label.set_text(time.strftime("%H", now))
            self.minutes_label.set_text(time.strftime("%M", now))
        return True

def main():
    kill_other_instances()
    stacked = "--stacked" in sys.argv or "-s" in sys.argv
    win = NothingClock(stacked=stacked)
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()

if __name__ == '__main__':
    main()
