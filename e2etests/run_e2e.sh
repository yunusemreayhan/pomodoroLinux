#!/usr/bin/env bash
# Run the full E2E test suite for pomodoroLinux.
# Automatically starts Xvfb on a free display so multiple instances
# can run in parallel on the same machine (CI-friendly).
#
# Usage: ./run_e2e.sh [pytest args...]
# Examples:
#   ./run_e2e.sh                    # run all tests
#   ./run_e2e.sh -k TestLogin -v    # run specific class
#   ./run_e2e.sh test_flows.py      # run specific file
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
VENV="$SCRIPT_DIR/.venv"

# ── Check prerequisites ─────────────────────────────────────────
for cmd in cargo tauri-driver WebKitWebDriver; do
    command -v "$cmd" >/dev/null 2>&1 || { echo "ERROR: $cmd not found"; exit 1; }
done
command -v Xvfb >/dev/null 2>&1 || { echo "ERROR: Xvfb not found (apt install xvfb)"; exit 1; }

# ── Ensure binaries ─────────────────────────────────────────────
DAEMON="$REPO_DIR/target/release/pomodoro-daemon"
if [ ! -f "$DAEMON" ]; then
    echo "Building pomodoro-daemon (release)..."
    (cd "$REPO_DIR" && cargo build --release -p pomodoro-daemon)
fi

GUI="${POMODORO_GUI_BINARY:-}"
if [ -z "$GUI" ]; then
    for candidate in \
        "$REPO_DIR/target/release/pomodoro-gui" \
        "$REPO_DIR/../pomodoroLinux/target/release/pomodoro-gui"; do
        if [ -f "$candidate" ]; then GUI="$candidate"; break; fi
    done
fi
if [ -z "$GUI" ] || [ ! -f "$GUI" ]; then
    echo "ERROR: pomodoro-gui binary not found. Build it or set POMODORO_GUI_BINARY."
    exit 1
fi

# ── Set up venv if needed ───────────────────────────────────────
if [ ! -d "$VENV" ]; then
    echo "Creating venv..."
    python3 -m venv "$VENV"
    "$VENV/bin/pip" install -q pytest pytest-rerunfailures
    if [ -d "$SCRIPT_DIR/tauriTester" ]; then
        "$VENV/bin/pip" install -q -e "$SCRIPT_DIR/tauriTester"
    fi
fi

# ── Start Xvfb on a free display ────────────────────────────────
# Pick a random display number (99-599) and retry if taken.
XVFB_PID=""
cleanup() {
    [ -n "$XVFB_PID" ] && kill "$XVFB_PID" 2>/dev/null || true
}
trap cleanup EXIT

for _ in $(seq 1 10); do
    DISPLAY_NUM=$((RANDOM % 500 + 99))
    if ! [ -e "/tmp/.X${DISPLAY_NUM}-lock" ]; then
        Xvfb ":${DISPLAY_NUM}" -screen 0 1280x720x24 &>/dev/null &
        XVFB_PID=$!
        sleep 0.5
        if kill -0 "$XVFB_PID" 2>/dev/null; then
            export DISPLAY=":${DISPLAY_NUM}"
            echo "Xvfb started on display $DISPLAY (pid $XVFB_PID)"
            break
        fi
        XVFB_PID=""
    fi
done

if [ -z "$XVFB_PID" ]; then
    echo "ERROR: Could not start Xvfb on any display"
    exit 1
fi

# ── Run tests ───────────────────────────────────────────────────
cd "$SCRIPT_DIR"
"$VENV/bin/python" -m pytest -v "$@"
