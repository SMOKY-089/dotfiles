#!/usr/bin/env python3
"""
Scalable Terminal Study Timer
Dynamically scales ASCII block digits to fill the terminal window.
Default: 100 minutes. Supports Spacebar pause, r to reset, +/- to adjust.
"""

import sys
import os
import time
import shutil
import select
import tty
import termios
import subprocess

# 5x5 Block Glyph Matrix
DIGITS = {
    '0': ['█████', '█   █', '█   █', '█   █', '█████'],
    '1': ['  ██ ', ' ███ ', '   █ ', '   █ ', ' █████'],
    '2': ['█████', '    █', '█████', '█    ', '█████'],
    '3': ['█████', '    █', ' ████', '    █', '█████'],
    '4': ['█   █', '█   █', '█████', '    █', '    █'],
    '5': ['█████', '█    ', '█████', '    █', '█████'],
    '6': ['█████', '█    ', '█████', '█   █', '█████'],
    '7': ['█████', '    █', '   █ ', '  █  ', '  █  '],
    '8': ['█████', '█   █', '█████', '█   █', '█████'],
    '9': ['█████', '█   █', '█████', '    █', '█████'],
    ':': ['     ', '  █  ', '     ', '  █  ', '     '],
    ' ': ['     ', '     ', '     ', '     ', '     '],
}

def parse_time_spec(arg):
    arg = arg.strip().lower()
    total = 0
    cur = ''
    has_unit = False
    for c in arg:
        if c.isdigit():
            cur += c
        elif c in ['h', 'm', 's']:
            has_unit = True
            val = int(cur) if cur else 0
            cur = ''
            if c == 'h': total += val * 3600
            elif c == 'm': total += val * 60
            elif c == 's': total += val
    if cur and not has_unit:
        total += int(cur) * 60  # Default to minutes if just a number
    return max(1, total)

def format_time(seconds):
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    else:
        return f"{m:02d}:{s:02d}"

def render_grid(text, scale_x, scale_y):
    grid = ['' for _ in range(5 * scale_y)]
    for char in text:
        glyph = DIGITS.get(char, DIGITS[' '])
        for r in range(5):
            expanded_row = ''.join(c * scale_x for c in glyph[r])
            for sy in range(scale_y):
                grid[r * scale_y + sy] += expanded_row + (' ' * max(1, scale_x // 2))
    return grid

def main():
    time_arg = sys.argv[1] if len(sys.argv) > 1 else "100m"
    total_seconds = parse_time_spec(time_arg)
    remaining = total_seconds
    paused = False
    title = f"STUDY SESSION ({time_arg.upper()})"

    # Save terminal settings
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    tty.setcbreak(fd)

    # Hide cursor and enter alternate screen
    sys.stdout.write("\033[?1049h\033[?25l")
    sys.stdout.flush()

    last_tick = time.time()

    try:
        while True:
            cols, rows = shutil.get_terminal_size((80, 24))
            time_str = format_time(remaining)

            # Calculate optimal scale to fill ~70% of screen
            num_chars = len(time_str)
            # Base width: 5 chars per glyph + spacing
            max_sx = max(1, (cols - 4) // (num_chars * 6))
            max_sy = max(1, (rows - 8) // 5)
            # Use proportional scale
            scale_x = min(max_sx, max(1, max_sy * 2))
            scale_y = max(1, scale_x // 2)

            grid = render_grid(time_str, scale_x, scale_y)
            rendered_height = len(grid)
            rendered_width = len(grid[0]) if grid else 0

            # Vertical padding to center
            pad_top = max(1, (rows - rendered_height - 4) // 2)

            # Colors: Wallust Slate (#91A5C1 / #887D75)
            TEXT_COLOR = "\033[38;2;145;165;193m"  # Slate Blue
            ACCENT_COLOR = "\033[38;2;136;125;117m" # Slate Gray
            PAUSE_COLOR = "\033[38;2;220;160;100m"  # Amber
            RESET = "\033[0m"

            output = ["\033[H\033[2J"] # Clear screen and move cursor home
            output.append("\n" * pad_top)

            # Title
            status_text = " [PAUSED] " if paused else " [RUNNING] "
            status_col = PAUSE_COLOR if paused else ACCENT_COLOR
            title_line = f"{ACCENT_COLOR}{title}{RESET} {status_col}{status_text}{RESET}"
            pad_title = max(0, (cols - len(title) - len(status_text) - 1) // 2)
            output.append(" " * pad_title + title_line + "\n\n")

            # Rendered block digits
            pad_left = max(0, (cols - rendered_width) // 2)
            for line in grid:
                output.append(" " * pad_left + TEXT_COLOR + line + RESET + "\n")

            # Bottom instruction bar
            output.append("\n")
            help_line = "[SPACE] Pause/Resume  •  [r] Reset  •  [+] +1m  •  [-] -1m  •  [q] Quit"
            pad_help = max(0, (cols - len(help_line)) // 2)
            output.append(" " * pad_help + ACCENT_COLOR + help_line + RESET)

            sys.stdout.write("".join(output))
            sys.stdout.flush()

            # Handle user keyboard input non-blocking
            r, _, _ = select.select([sys.stdin], [], [], 0.25)
            if r:
                ch = sys.stdin.read(1)
                if ch in ['q', 'Q', '\x03']: # q or Ctrl+C
                    break
                elif ch == ' ':
                    paused = not paused
                elif ch in ['r', 'R']:
                    remaining = total_seconds
                    paused = False
                elif ch == '+':
                    remaining += 60
                elif ch == '-':
                    remaining = max(0, remaining - 60)

            # Countdown ticker
            now = time.time()
            if not paused:
                delta = now - last_tick
                if delta >= 1.0:
                    remaining = max(0, remaining - int(delta))
                    last_tick = now
                    if remaining == 0:
                        # Play notification sound and alert
                        subprocess.run(["notify-send", "-u", "critical", "Study Session Completed!", "Time to take a break."], check=False)
                        subprocess.run(["pw-play", "/usr/share/sounds/freedesktop/stereo/complete.oga"], check=False)
                        paused = True
            else:
                last_tick = now

    finally:
        # Restore terminal state
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        sys.stdout.write("\033[?1049l\033[?25h")
        sys.stdout.flush()

if __name__ == "__main__":
    main()
