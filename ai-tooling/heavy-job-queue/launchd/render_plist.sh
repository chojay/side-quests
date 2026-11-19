#!/bin/sh
# Render the watchdog LaunchAgent plist for this user and print how to load it.
# It writes one file and runs no launchctl command: loading a background agent is
# a decision for the person at the keyboard.
#
#   launchd/render_plist.sh [OUT_DIR]      (default OUT_DIR: current directory)
set -eu
HERE=$(cd "$(dirname "$0")" && pwd)
ROOT=$(dirname "$HERE")
OUT_DIR=${1:-.}
LABEL=${MEMGUARD_LABEL:-local.memguard.watchdog}
PY=${MEMGUARD_PYTHON:-/usr/bin/python3}
CONFIG=${MEMGUARD_CONFIG:-$HOME/.config/memguard/config.json}
STATE=${MEMGUARD_STATE:-$HOME/.local/state/memguard}
OUT="$OUT_DIR/$LABEL.plist"
mkdir -p "$OUT_DIR"
sed -e "s|__LABEL__|$LABEL|g" -e "s|__PYTHON__|$PY|g" -e "s|__SCRIPT__|$ROOT/mem_watchdog.py|g" \
    -e "s|__USER__|$(id -un)|g" -e "s|__CONFIG__|$CONFIG|g" -e "s|__STATE__|$STATE|g" \
    "$HERE/mem-watchdog.plist.template" > "$OUT"
if command -v plutil >/dev/null 2>&1; then plutil -lint "$OUT"; fi
cat <<MSG
Wrote $OUT. Read it, then, if you want the watchdog running:
  mkdir -p "$STATE"
  cp "$OUT" "$HOME"/Library/LaunchAgents/
  launchctl bootstrap gui/\$(id -u) "$HOME"/Library/LaunchAgents/$LABEL.plist
Status:  $PY "$ROOT/mem_watchdog.py" --status
Remove:  launchctl bootout gui/\$(id -u)/$LABEL
MSG
