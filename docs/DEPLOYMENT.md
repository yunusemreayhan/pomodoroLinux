# Deployment Guide

## Prerequisites
- Rust 1.75+ (for building the daemon)
- Node.js 18+ (for building the GUI)
- SQLite 3.35+ (bundled via sqlx)

## Build

### Backend
```bash
cargo build --release -p pomodoro-daemon
# Binary: target/release/pomodoro-daemon
```

### Frontend (Tauri desktop app)
```bash
cd gui
npm install
npm run tauri build
# Output: gui/src-tauri/target/release/bundle/
```

## Configuration

1. Copy default config: `mkdir -p ~/.config/pomodoro && cp config.example.toml ~/.config/pomodoro/config.toml`
2. Set environment variables (see [ENV_VARS.md](ENV_VARS.md))
3. Key settings:
   - `POMODORO_JWT_SECRET` — set a stable secret for production
   - `POMODORO_ROOT_PASSWORD` — change from default before first run
   - `POMODORO_CORS_ORIGINS` — restrict to your frontend origin

## Run

```bash
# Start daemon
./target/release/pomodoro-daemon

# Or with structured logging
POMODORO_LOG_JSON=1 ./target/release/pomodoro-daemon
```

The daemon creates its SQLite database at `~/.local/share/pomodoro/pomodoro.db` on first run.

## Systemd Service (Linux)

```ini
[Unit]
Description=Pomodoro Daemon
After=network.target

[Service]
Type=simple
ExecStart=/usr/local/bin/pomodoro-daemon
Environment=POMODORO_JWT_SECRET=your-secret-here
Environment=POMODORO_LOG_JSON=1
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

## Health Check

```bash
curl http://localhost:3030/api/health
# {"status":"ok","db":true,"active_timers":0}
```

## Backup

The SQLite database is a single file. Back it up with:
```bash
sqlite3 ~/.local/share/pomodoro/pomodoro.db ".backup /path/to/backup.db"
```

Attachments are stored in `~/.local/share/pomodoro/attachments/`.
