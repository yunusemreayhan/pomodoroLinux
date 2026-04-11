# Changelog

## v4 (in progress)

### Security
- JWT secret file permissions set to 0600
- Token type field in JWT Claims (access vs refresh separation)
- Rate limiting on refresh endpoint
- Removed legacy SSE ?token= query parameter (ticket-only)
- Rate limiter fallback for missing IP headers
- Improved SSRF check for webhook URLs (169.254, .local, 172.16-31)
- SHA-256 for token blocklist hashing (was DefaultHasher)
- SHA-256 for webhook HMAC signatures (was DefaultHasher)
- Username validation in profile update
- Password max length 128 chars

### Bug Fixes
- tick() uses per-user config instead of global config
- skip() advances to next phase instead of stopping
- cancel_burn validates sprint_id matches
- SSE notifications for leave_room, start_voting, assignees, comments
- retro_notes textarea updates on SSE push
- stop_session logs errors instead of silently ignoring
- Sprint delete confirmation dialog
- SSE debounce timer cleared on unmount
- Attachment upload/download uses store auth (was broken globals)
- customAccept NaN validation
- AdminPanel null-checks API response
- TeamManager uses /api/users (was /api/admin/users)
- team_id filter included in task count query

### Authorization & Validation
- Sprint task add/remove requires sprint owner
- Config bounds validation (timer durations, daily goal)
- Sprint/room name validation (non-empty, max 200)
- Estimation unit validation (points/hours/mandays)
- Vote value range validation (0-1000)
- Non-negative burn points/hours
- Positive time report hours
- Non-empty comment content
- estimation_mode validated (hours/points)

### Features
- Break duration display on timer buttons
- Password visibility toggle on auth screen
- Leave room button for non-admin members
- Sprint start/complete confirmation dialogs

### Accessibility
- Context menu: Escape key, ARIA roles (menu/menuitem)
- Toggle: role=switch, aria-checked
- Timer buttons: aria-labels
- Auth form: aria-labels, error role=alert
- Sprint list: keyboard accessible (role=button, tabIndex, Enter)

### Code Quality
- PRIORITY_COLORS extracted to shared constants
- Status constants with TypeScript union types
- Removed unused imports and dead code
- Module-level variables instead of (window as any) globals
- Snapshot errors logged instead of silently ignored

---

## v3

### Highlights
- 78 items completed across bugs, security, features, performance,
  code quality, UX, accessibility, tests, and documentation
- JWT refresh tokens with rotation
- File attachments (upload/download/delete)
- i18n framework with English locale
- Task archiving, velocity charts, sprint board drag-and-drop
- Component splitting (TaskContextMenu, SprintViews)
- 97 backend tests, 44 frontend tests

---

## v2

### Highlights
- 61 items completed
- Estimation rooms with planning poker
- Sprint burndown charts and burn tracking
- Epic groups and team management
- Task dependencies and labels
- Recurrence rules
- Webhook system
- CSV/JSON export

---

## v1

### Initial Release
- Multi-user Pomodoro timer with Rust/axum backend
- Tauri v2 desktop app (React/TypeScript)
- SQLite database with WAL mode
- Hierarchical tasks with drag-and-drop
- Sprint management
- Real-time SSE updates
- JWT authentication
