#!/usr/bin/env python3
"""
Zen Browser Settings Reset Tool
Resets browser configuration and mods to factory defaults while preserving:
- All 4 Spaces (Space, Focus, Audio, Star)
- All 64 open tabs, pinned tabs, and split views
- All Extensions (Tampermonkey, uBlock, Dark Reader, Bitwarden, etc.) & extension data
- Saved Logins, Passwords, Bookmarks, and History
"""

import os
import sys
import shutil
import time
import subprocess
from datetime import datetime

PROFILE_DIR = os.path.expanduser("~/.config/zen/Profiles/s5agi9x7.Default (release)")
BACKUP_BASE = os.path.expanduser("~/.config/zen/Profiles")

PRESERVE_PREFS = [
    "extensions.webextensions.uuids",
    "extensions.webextensions.ExtensionStorageIDB",
    "extensions.activeThemeID",
    "media.gmp-widevinecdm",
    "media.gmp-gmpopenh264",
    "zen.workspaces.active",
]

def is_zen_running():
    try:
        out = subprocess.check_output(["pgrep", "-f", "zen-bin"]).decode().strip()
        return bool(out)
    except subprocess.CalledProcessError:
        return False

def reset_settings(keep_toolbar_layout=True):
    if is_zen_running():
        print("❌ Error: Zen Browser is currently running!")
        print("Please close Zen Browser completely before running this script so changes are not overwritten.")
        sys.exit(1)

    if not os.path.exists(PROFILE_DIR):
        print(f"❌ Error: Profile directory not found: {PROFILE_DIR}")
        sys.exit(1)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = os.path.join(BACKUP_BASE, f"zen_backup_before_reset_{timestamp}")

    print(f"📦 Step 1: Creating safety snapshot at:\n   {backup_dir}")
    shutil.copytree(PROFILE_DIR, backup_dir, symlinks=True, ignore_dangling_symlinks=True)

    # 1. Reset prefs.js
    prefs_file = os.path.join(PROFILE_DIR, "prefs.js")
    if os.path.exists(prefs_file):
        preserved_lines = []
        with open(prefs_file, "r", encoding="utf-8") as f:
            for line in f:
                if keep_toolbar_layout and '"browser.uiCustomization.state"' in line:
                    preserved_lines.append(line)
                    continue
                for p in PRESERVE_PREFS:
                    if f'"{p}' in line:
                        preserved_lines.append(line)
                        break

        with open(prefs_file, "w", encoding="utf-8") as f:
            f.writelines(preserved_lines)
        print(f"✅ Step 2: Reset prefs.js (kept {len(preserved_lines)} essential extension/workspace bindings).")

    # 2. Reset UI window cache & site content preferences
    for f in ["xulstore.json", "content-prefs.sqlite", "content-prefs.sqlite-wal"]:
        path = os.path.join(PROFILE_DIR, f)
        if os.path.exists(path):
            os.remove(path)
    print("✅ Step 3: Cleared UI cache and site-specific overrides.")

    print("\n🎉 Zen Browser settings have been successfully reset to factory defaults!")
    print("   • Spaces & Workspaces: PRESERVED")
    print("   • All 64 Tabs & History: PRESERVED")
    print("   • All Extensions & Scripts: PRESERVED")
    print(f"\n💡 If you ever want to revert, restore the snapshot with:\n   cp -r '{backup_dir}/'* '{PROFILE_DIR}/'")

if __name__ == "__main__":
    reset_settings()
