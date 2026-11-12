#!/usr/bin/env python3
"""
Wayland Floating Media Control Center Widget
Designed for Niri & Waybar with multi-player support, album artwork,
timeline scrubbing, independent volume mixing, and animated audio spectrum visualizer.
"""

import os
import sys
import math
import random
import urllib.parse
import cairo
import gi

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
gi.require_version('GdkPixbuf', '2.0')
gi.require_version('GtkLayerShell', '0.1')
gi.require_version('Playerctl', '2.0')

from gi.repository import Gtk, Gdk, GLib, GdkPixbuf, GtkLayerShell, Playerctl

def format_time(seconds):
    if not seconds or seconds < 0:
        return "0:00"
    m = int(seconds // 60)
    s = int(seconds % 60)
    return f"{m}:{s:02d}"

class VisualizerWidget(Gtk.DrawingArea):
    def __init__(self, num_bars=22):
        super().__init__()
        self.num_bars = num_bars
        self.heights = [0.1] * num_bars
        self.targets = [0.1] * num_bars
        self.is_playing = False
        self.tick_count = 0

        self.set_size_request(180, 32)
        self.connect("draw", self.on_draw)

    def set_playing(self, playing):
        self.is_playing = playing

    def update_animation(self):
        self.tick_count += 1
        for i in range(self.num_bars):
            if self.is_playing:
                # Dynamic multi-sine wave frequency simulation with natural jitter
                wave1 = math.sin(self.tick_count * 0.15 + i * 0.4)
                wave2 = math.cos(self.tick_count * 0.25 - i * 0.6)
                rand_flux = random.uniform(-0.15, 0.15)
                val = 0.45 + (wave1 * 0.3) + (wave2 * 0.2) + rand_flux
                self.targets[i] = max(0.12, min(0.95, val))
            else:
                self.targets[i] = 0.08

            # Smooth interpolation
            self.heights[i] += (self.targets[i] - self.heights[i]) * 0.35

        self.queue_draw()
        return True

    def on_draw(self, widget, cr):
        width = widget.get_allocated_width()
        height = widget.get_allocated_height()

        bar_spacing = 2.5
        total_spacing = bar_spacing * (self.num_bars - 1)
        bar_width = max(3.0, (width - total_spacing) / self.num_bars)

        for i in range(self.num_bars):
            x = i * (bar_width + bar_spacing)
            if self.is_playing:
                bar_h = max(3.0, self.heights[i] * height)
            else:
                bar_h = 3.0
            y = height - bar_h

            pat = cairo.LinearGradient(x, y, x, height)
            if self.is_playing:
                # Wallust foreground #91A5C1 (top) to Wallust accent #887D75 (base)
                pat.add_color_stop_rgba(0.0, 0.57, 0.65, 0.76, 0.95)
                pat.add_color_stop_rgba(1.0, 0.53, 0.49, 0.46, 0.85)
            else:
                # Muted idle baseline #4C5F79 / #373736
                pat.add_color_stop_rgba(0.0, 0.30, 0.37, 0.47, 0.7)
                pat.add_color_stop_rgba(1.0, 0.22, 0.22, 0.21, 0.4)

            cr.set_source(pat)
            # Sharp brutalist rectangle (consistent with 0 border-radius setup)
            cr.rectangle(x, y, bar_width, bar_h)
            cr.fill()

        return False

class MediaCardWindow(Gtk.Window):
    def __init__(self):
        super().__init__()
        self.set_title("Media Control Center")

        # Initialize as Wayland Layer Shell
        GtkLayerShell.init_for_window(self)
        GtkLayerShell.set_namespace(self, "media-card")
        GtkLayerShell.set_layer(self, GtkLayerShell.Layer.TOP)
        GtkLayerShell.set_keyboard_mode(self, GtkLayerShell.KeyboardMode.ON_DEMAND)
        GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.LEFT, True)
        GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.TOP, False)
        GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.BOTTOM, False)
        GtkLayerShell.set_margin(self, GtkLayerShell.Edge.LEFT, 48)

        # Transparent RGBA visual
        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        if visual:
            self.set_visual(visual)

        self.manager = Playerctl.PlayerManager()
        self.active_player = None
        self.seeking = False

        self.setup_ui()
        self.setup_css()
        self.connect("key-press-event", self.on_key_press)

        # Refresh timers
        GLib.timeout_add(50, self.visualizer.update_animation)
        GLib.timeout_add(500, self.update_progress)
        GLib.timeout_add(1000, self.refresh_players)

        self.refresh_players()

    def setup_ui(self):
        # Card Container
        self.card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        self.card.get_style_context().add_class("media-card")
        self.add(self.card)

        # Header Row: Player Selector Tabs + Close Button
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.player_tabs_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        header.pack_start(self.player_tabs_box, True, True, 0)

        close_btn = Gtk.Button(label="✕")
        close_btn.get_style_context().add_class("close-btn")
        close_btn.connect("clicked", lambda b: Gtk.main_quit())
        header.pack_end(close_btn, False, False, 0)
        self.card.pack_start(header, False, False, 0)

        # Track Info Row: Album Art + (Title, Artist, Visualizer)
        info_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)

        # Artwork Image (80x80)
        self.art_image = Gtk.Image()
        self.art_image.get_style_context().add_class("album-art")
        self.art_image.set_size_request(84, 84)
        info_row.pack_start(self.art_image, False, False, 0)

        meta_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self.title_label = Gtk.Label(label="No Media Playing")
        self.title_label.set_xalign(0)
        self.title_label.set_ellipsize(3) # PANGO_ELLIPSIZE_END
        self.title_label.set_max_width_chars(36)
        self.title_label.get_style_context().add_class("track-title")

        self.artist_label = Gtk.Label(label="Select a player")
        self.artist_label.set_xalign(0)
        self.artist_label.set_ellipsize(3)
        self.artist_label.set_max_width_chars(36)
        self.artist_label.get_style_context().add_class("track-artist")

        self.visualizer = VisualizerWidget(num_bars=22)

        meta_box.pack_start(self.title_label, False, False, 0)
        meta_box.pack_start(self.artist_label, False, False, 0)
        meta_box.pack_start(self.visualizer, False, False, 4)
        info_row.pack_start(meta_box, True, True, 0)

        self.card.pack_start(info_row, False, False, 0)

        # Timeline Slider + Timestamps
        timeline_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        self.progress_scale = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL)
        self.progress_scale.set_range(0, 100)
        self.progress_scale.set_draw_value(False)
        self.progress_scale.get_style_context().add_class("timeline-slider")
        self.progress_scale.connect("change-value", self.on_timeline_seek)

        time_labels_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.time_curr = Gtk.Label(label="0:00")
        self.time_curr.get_style_context().add_class("time-text")
        self.time_total = Gtk.Label(label="0:00")
        self.time_total.get_style_context().add_class("time-text")

        time_labels_box.pack_start(self.time_curr, False, False, 0)
        time_labels_box.pack_end(self.time_total, False, False, 0)

        timeline_box.pack_start(self.progress_scale, False, False, 0)
        timeline_box.pack_start(time_labels_box, False, False, 0)
        self.card.pack_start(timeline_box, False, False, 0)

        # Bottom Row: Transport Controls (Left/Center) + Volume Slider (Right)
        bottom_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=14)

        controls_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.prev_btn = Gtk.Button(label="󰒮")
        self.prev_btn.get_style_context().add_class("ctrl-btn")
        self.prev_btn.connect("clicked", lambda b: self.active_player and self.active_player.previous())

        self.play_btn = Gtk.Button(label="󰐊")
        self.play_btn.get_style_context().add_class("play-btn")
        self.play_btn.connect("clicked", self.on_play_pause)

        self.next_btn = Gtk.Button(label="󰒭")
        self.next_btn.get_style_context().add_class("ctrl-btn")
        self.next_btn.connect("clicked", lambda b: self.active_player and self.active_player.next())

        controls_box.pack_start(self.prev_btn, False, False, 0)
        controls_box.pack_start(self.play_btn, False, False, 0)
        controls_box.pack_start(self.next_btn, False, False, 0)
        bottom_row.pack_start(controls_box, False, False, 0)

        # Dedicated Player Volume Slider
        vol_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        vol_icon = Gtk.Label(label="󰕾")
        vol_icon.get_style_context().add_class("vol-icon")

        self.vol_scale = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL)
        self.vol_scale.set_range(0, 100)
        self.vol_scale.set_draw_value(False)
        self.vol_scale.set_size_request(110, -1)
        self.vol_scale.get_style_context().add_class("volume-slider")
        self.vol_scale.connect("value-changed", self.on_volume_changed)

        vol_box.pack_start(vol_icon, False, False, 0)
        vol_box.pack_start(self.vol_scale, True, True, 0)
        bottom_row.pack_end(vol_box, True, True, 0)

        self.card.pack_start(bottom_row, False, False, 0)

    def setup_css(self):
        provider = Gtk.CssProvider()
        css = """
        * {
            font-family: 'JetBrainsMono Nerd Font Propo', 'JetBrainsMono Nerd Font', monospace;
            border-radius: 0px;
            box-shadow: none;
        }

        window {
            background-color: transparent;
        }

        .media-card {
            background-color: #0F1010;
            border: 2px solid #887D75;
            padding: 16px 18px;
            min-width: 420px;
        }

        /* Player Tabs / Switcher */
        .player-pill {
            background-color: transparent;
            border: 1px solid #4C5F79;
            color: #7F837C;
            font-size: 11px;
            font-weight: 600;
            padding: 4px 10px;
            margin-right: 4px;
        }

        .player-pill:hover {
            background-color: #373736;
            color: #91A5C1;
            border-color: #717782;
        }

        .player-pill.active {
            background-color: #887D75;
            color: #0F1010;
            border-color: #887D75;
            font-weight: 700;
        }

        /* Close Button */
        .close-btn {
            background-color: transparent;
            border: 1px solid #4C5F79;
            color: #7F837C;
            font-size: 12px;
            min-width: 24px;
            min-height: 24px;
            padding: 2px 6px;
        }

        .close-btn:hover {
            background-color: #373736;
            color: #B3BCCA;
            border-color: #887D75;
        }

        /* Album Artwork */
        .album-art {
            border: 1px solid #887D75;
            background-color: #0F1010;
        }

        /* Metadata Typography */
        .track-title {
            color: #B3BCCA;
            font-size: 13px;
            font-weight: 700;
            letter-spacing: -0.2px;
        }

        .track-artist {
            color: #91A5C1;
            font-size: 11px;
            font-weight: 500;
        }

        .time-text {
            color: #717782;
            font-size: 10px;
        }

        /* Transport Controls */
        .ctrl-btn {
            background-color: transparent;
            border: 1px solid #4C5F79;
            color: #91A5C1;
            font-size: 14px;
            min-width: 36px;
            min-height: 32px;
            padding: 0;
        }

        .ctrl-btn:hover {
            background-color: #373736;
            border-color: #887D75;
            color: #B3BCCA;
        }

        .play-btn {
            background-color: #887D75;
            border: 1px solid #887D75;
            color: #0F1010;
            font-size: 15px;
            min-width: 44px;
            min-height: 32px;
            padding: 0;
        }

        .play-btn:hover {
            background-color: #91A5C1;
            border-color: #91A5C1;
            color: #0F1010;
        }

        .vol-icon {
            color: #887D75;
            font-size: 14px;
        }

        /* Sliders (Timeline & Volume) */
        scale trough {
            background-color: #373736;
            background-image: none;
            min-height: 4px;
            border: none;
        }

        scale trough highlight,
        scale highlight {
            background-color: #887D75;
            background-image: none;
            min-height: 4px;
            border: none;
        }

        scale slider {
            min-height: 12px;
            min-width: 6px;
            background-color: #91A5C1;
            background-image: none;
            border: 1px solid #0F1010;
            margin: -4px 0;
        }

        scale slider:hover {
            background-color: #B3BCCA;
        }
        """
        provider.load_from_data(css.encode())
        Gtk.StyleContext.add_provider_for_screen(
            self.get_screen(),
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def refresh_players(self):
        raw_players = list(self.manager.props.player_names)

        # Clear existing tabs
        for child in self.player_tabs_box.get_children():
            self.player_tabs_box.remove(child)

        if not raw_players:
            self.title_label.set_text("No Media Playing")
            self.artist_label.set_text("Launch YouTube / Spotify / mpv")
            self.visualizer.set_playing(False)
            self.active_player = None
            return True

        # Deduplicate: If Plasma Browser Integration is active, ignore Chromium's duplicate native MPRIS stream
        has_plasma = any("plasma" in p.name.lower() for p in raw_players)
        player_names = []
        for p in raw_players:
            lower = p.name.lower()
            if has_plasma and ("brave" in lower or "chromium" in lower or "chrome" in lower):
                continue
            player_names.append(p)

        if not player_names:
            player_names = raw_players

        found_active = False
        for p_name in player_names:
            btn = Gtk.Button(label=self.format_player_name(p_name.name))
            btn.get_style_context().add_class("player-pill")

            if self.active_player and self.active_player.props.player_name == p_name.name:
                btn.get_style_context().add_class("active")
                found_active = True

            btn.connect("clicked", lambda b, name=p_name: self.switch_to_player(name))
            self.player_tabs_box.pack_start(btn, False, False, 0)

        self.player_tabs_box.show_all()

        if not found_active or self.active_player is None:
            # Default to first player
            self.switch_to_player(player_names[0])
        else:
            self.sync_active_player_state()

        return True

    def format_player_name(self, raw_name):
        lower = raw_name.lower()
        if "plasma" in lower or "brave" in lower:
            return "YouTube / Brave"
        elif "firefox" in lower or "zen" in lower:
            return "Lecture / Zen"
        elif "chrome" in lower:
            return "Chrome"
        elif "mpv" in lower:
            return "mpv Player"
        elif "spotify" in lower:
            return "Spotify"
        return raw_name.split('.')[0][:14]

    def switch_to_player(self, player_name_obj):
        self.active_player = Playerctl.Player.new_from_name(player_name_obj)
        self.sync_active_player_state()
        self.refresh_players()

    def sync_active_player_state(self):
        if not self.active_player:
            return

        # Title & Artist
        title = self.active_player.get_title() or "Unknown Title"
        artist = self.active_player.get_artist() or "Unknown Artist"
        self.title_label.set_text(title)
        self.title_label.set_tooltip_text(title)
        self.artist_label.set_text(artist)

        # Status & Play/Pause Icon
        status = self.active_player.props.playback_status
        is_playing = (status == Playerctl.PlaybackStatus.PLAYING)
        self.play_btn.set_label("󰏤" if is_playing else "󰐊")
        self.visualizer.set_playing(is_playing)

        # Volume
        vol = self.active_player.props.volume
        if vol is not None:
            self.vol_scale.handler_block_by_func(self.on_volume_changed)
            self.vol_scale.set_value(vol * 100.0)
            self.vol_scale.handler_unblock_by_func(self.on_volume_changed)

        # Artwork
        art_url = self.active_player.print_metadata_prop('mpris:artUrl')
        self.load_artwork(art_url)

    def load_artwork(self, art_url):
        if not art_url:
            self.art_image.set_from_icon_name("audio-x-generic", Gtk.IconSize.DIALOG)
            return

        try:
            parsed = urllib.parse.urlparse(art_url)
            local_path = urllib.parse.unquote(parsed.path)
            if os.path.exists(local_path):
                pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(local_path, 84, 84, True)
                self.art_image.set_from_pixbuf(pixbuf)
            else:
                self.art_image.set_from_icon_name("audio-x-generic", Gtk.IconSize.DIALOG)
        except Exception:
            self.art_image.set_from_icon_name("audio-x-generic", Gtk.IconSize.DIALOG)

    def update_progress(self):
        if not self.active_player or self.seeking:
            return True

        try:
            pos_us = self.active_player.get_position()
            len_str = self.active_player.print_metadata_prop('mpris:length')

            if len_str and int(len_str) > 0:
                len_sec = int(len_str) / 1_000_000.0
                pos_sec = pos_us / 1_000_000.0

                self.time_curr.set_text(format_time(pos_sec))
                self.time_total.set_text(format_time(len_sec))

                self.progress_scale.set_range(0, len_sec)
                self.progress_scale.set_value(pos_sec)
            else:
                self.time_curr.set_text("Live")
                self.time_total.set_text("Stream")
                self.progress_scale.set_range(0, 100)
                self.progress_scale.set_value(0)
        except Exception:
            pass

        return True

    def on_timeline_seek(self, scale, scroll, value):
        if self.active_player:
            self.seeking = True
            pos_us = int(value * 1_000_000)
            self.active_player.set_position(pos_us)
            self.seeking = False
        return False

    def on_volume_changed(self, scale):
        if self.active_player:
            new_vol = scale.get_value() / 100.0
            self.active_player.set_volume(new_vol)

    def on_play_pause(self, btn):
        if self.active_player:
            self.active_player.play_pause()
            GLib.timeout_add(100, self.sync_active_player_state)

    def on_key_press(self, widget, event):
        if event.keyval == Gdk.KEY_Escape:
            Gtk.main_quit()
            return True
        return False

PID_FILE = "/tmp/media-card.pid"
LOG_FILE = "/tmp/media-card.log"

def log(msg):
    try:
        import time
        with open(LOG_FILE, "a") as f:
            f.write(f"[{time.strftime('%X')}] {msg}\n")
    except Exception:
        pass

def main():
    import signal
    log(f"Invoked with args: {sys.argv} (PID {os.getpid()})")

    if "toggle" in sys.argv:
        if os.path.exists(PID_FILE):
            try:
                with open(PID_FILE, "r") as f:
                    old_pid = int(f.read().strip())
                # Verify if process is actually alive
                os.kill(old_pid, 0)
                # If alive, kill it and exit
                log(f"Toggling off running instance PID {old_pid}")
                os.kill(old_pid, signal.SIGTERM)
                try:
                    os.remove(PID_FILE)
                except Exception:
                    pass
                sys.exit(0)
            except (ProcessLookupError, ValueError):
                # Process is not alive, clean stale PID file
                log("Stale PID file detected; cleaning up and launching fresh")
                try:
                    os.remove(PID_FILE)
                except Exception:
                    pass
            except Exception as e:
                log(f"Error checking PID file: {e}")
                try:
                    os.remove(PID_FILE)
                except Exception:
                    pass

    with open(PID_FILE, "w") as f:
        f.write(str(os.getpid()))

    try:
        win = MediaCardWindow()
        win.connect("destroy", Gtk.main_quit)
        win.show_all()
        log("MediaCardWindow launched and entering Gtk.main()")
        Gtk.main()
    finally:
        log("Exiting Gtk.main(), removing PID file")
        if os.path.exists(PID_FILE):
            try:
                os.remove(PID_FILE)
            except Exception:
                pass

if __name__ == '__main__':
    main()
