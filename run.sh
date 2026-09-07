#!/bin/bash
# NekoDesk 3D Launcher
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

# Clean up any previously running MewDestop instance
PREV_PIDS=$(pgrep -f "godot.*MewDestop" || true)
if [ -n "$PREV_PIDS" ]; then
    echo "🧹 Closing previous NekoDesk 3D instance..."
    echo "$PREV_PIDS" | xargs kill 2>/dev/null || true
    sleep 0.3
fi

# Find Godot executable
if command -v godot &> /dev/null; then
    GODOT_BIN="godot"
elif [ -f "/Applications/Godot.app/Contents/MacOS/Godot" ]; then
    GODOT_BIN="/Applications/Godot.app/Contents/MacOS/Godot"
else
    echo "❌ Godot not found in PATH or /Applications/Godot.app"
    echo "Please install Godot 4: brew install --cask godot"
    exit 1
fi

echo "🐾 Launching NekoDesk 3D with: $GODOT_BIN"
exec "$GODOT_BIN" --path "$DIR" "$@"
