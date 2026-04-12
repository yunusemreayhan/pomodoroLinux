# Contributing

## Development Setup

### Prerequisites
- Rust 1.75+ with `cargo`
- Node.js 18+ with `npm`
- SQLite 3.35+ (for WAL mode and RETURNING)

### Backend
```bash
cd crates/pomodoro-daemon
cargo build
cargo test
```

### Frontend
```bash
cd gui
npm install
npx tsc --noEmit   # type check
npm test            # run tests
npm run dev         # dev server (Tauri)
```

### Running
```bash
cargo run -p pomodoro-daemon   # starts on :3030
cd gui && npm run tauri dev    # starts Tauri app
```

## Code Style

- Rust: `cargo fmt` + `cargo clippy`
- TypeScript: strict mode, no `any` (except test mocks)
- Minimal code — only what's needed to solve the problem
- Comments for non-obvious logic only

## Testing

- Backend: integration tests in `tests/api_tests.rs` (186 tests)
- Frontend: unit tests in `gui/src/__tests__/` (134 tests)
- Run both before submitting: `cargo test -p pomodoro-daemon && cd gui && npm test`

## Project Structure

```
crates/pomodoro-daemon/
  src/
    routes/     # HTTP route handlers (24 files)
    db/         # Database queries (19 files)
    engine.rs   # Timer state machine
    auth.rs     # JWT auth + token blocklist
    config.rs   # Config file management
    webhook.rs  # Webhook dispatch
gui/
  src/
    components/ # React components
    store/      # Zustand store + API layer
    __tests__/  # Frontend tests
docs/           # Documentation
```
