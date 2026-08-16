#!/usr/bin/env python3
import os
import sys
import subprocess
from pathlib import Path

# Paths
SCRIPTS_DIR = Path(__file__).parent.resolve()
PLIST_PATH = Path.home() / "Library/LaunchAgents/com.jeffliu.tg_listener.plist"
SCRIPT_PATH = SCRIPTS_DIR / "tg_listener.py"
PYTHON_PATH = "/usr/bin/python3"
WORKING_DIR = SCRIPTS_DIR

PLIST_TEMPLATE = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.jeffliu.tg_listener</string>
    <key>ProgramArguments</key>
    <array>
        <string>{PYTHON_PATH}</string>
        <string>{SCRIPT_PATH}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>WorkingDirectory</key>
    <string>{WORKING_DIR}</string>
    <key>StandardErrorPath</key>
    <string>/tmp/tg_listener.err</string>
    <key>StandardOutPath</key>
    <string>/tmp/tg_listener.out</string>
</dict>
</plist>
"""

def enable():
    # Write plist
    PLIST_PATH.parent.mkdir(parents=True, exist_ok=True)
    PLIST_PATH.write_text(PLIST_TEMPLATE)
    print(f"Created {PLIST_PATH}")
    
    # Load service
    try:
        subprocess.run(["launchctl", "load", str(PLIST_PATH)], check=True)
        print("Service loaded and started.")
    except subprocess.CalledProcessError:
        # If already loaded, try unloading and reloading
        subprocess.run(["launchctl", "unload", str(PLIST_PATH)], capture_output=True)
        subprocess.run(["launchctl", "load", str(PLIST_PATH)], check=True)
        print("Service reloaded and started.")

def disable():
    if PLIST_PATH.exists():
        subprocess.run(["launchctl", "unload", str(PLIST_PATH)], capture_output=True)
        PLIST_PATH.unlink()
        print("Service stopped and configuration removed.")
    else:
        print("No service configuration found.")

def status():
    result = subprocess.run(["launchctl", "list", "com.jeffliu.tg_listener"], capture_output=True, text=True)
    if result.returncode == 0:
        print("Service is running.")
    else:
        print("Service is not running.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: manage_service.py [enable|disable|status]")
        sys.exit(1)
    
    cmd = sys.argv[1]
    if cmd == "enable":
        enable()
    elif cmd == "disable":
        disable()
    elif cmd == "status":
        status()
    else:
        print(f"Unknown command: {cmd}")
