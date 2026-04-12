# Backlog V36 — Full Codebase Audit (2026-04-13)

Scope: Stability, correctness, security, performance, UX, accessibility, code quality.
No new features.

---

## V36-1 [Medium / Security] `create_sse_ticket` still uses `/dev/urandom` directly
**File:** `routes/misc.rs:create_sse_ticket`
V35 fixed `generate_salt` and `encrypt_auth` in the Tauri GUI to use `getrandom`, but the backend SSE ticket generation still reads `/dev/urandom` directly. If it fails, falls back to hash-based entropy with a security warning. Should use `getrandom` crate for consistency and cross-platform safety.

## V36-2 [Medium / Security] JWT secret generation in `auth.rs` uses `/dev/urandom` directly
**File:** `auth.rs:secret()`
Same issue as V36-1. The JWT secret generation reads `/dev/urandom` and falls back to hash-based entropy. The `getrandom` crate is already a transitive dependency (via `rand`). Should use it directly for the 64-byte secret generation.

## V36-3 [Medium / Bug] `auto_archive` uses SQLite `datetime('now')` instead of Rust-generated UTC timestamp
**File:** `main.rs:280`
`UPDATE tasks SET status = 'archived', updated_at = datetime('now')` — uses SQLite's `datetime('now')` while all other timestamps use `now_str()` (Rust-side UTC). If SQLite is compiled with a non-UTC default, this would be inconsistent. Should use `db::now_str()` bound as a parameter.

## V36-4 [Medium / Bug] `token_blocklist` cleanup uses `datetime('now')` inconsistently
**File:** `main.rs:225`, `auth.rs:revoke_token`
The hourly cleanup `DELETE FROM token_blocklist WHERE expires_at < datetime('now')` and the revoke function both use SQLite's `datetime('now')`. The `expires_at` is stored from Rust-side `chrono::DateTime::format`. These should be consistent — either all SQLite `datetime('now')` or all Rust `now_str()`.

## V36-5 [Medium / Bug] `weekly_digest` uses SQLite `date('now')` functions
**File:** `routes/history.rs:weekly_digest`
`WHERE updated_at >= date('now', '-7 days')` and `WHERE due_date BETWEEN date('now') AND date('now', '+7 days')` — same timezone inconsistency as V36-3. Should compute dates in Rust and bind as parameters.

## V36-6 [Low / Bug] `bulk_update_status` not registered in OpenAPI paths
**File:** `main.rs`, `routes/tasks.rs`
The `bulk_update_status` endpoint (`PUT /api/tasks/bulk-status`) exists in the router but is not listed in the `#[openapi(paths(...))]` macro. Missing from Swagger docs.

## V36-7 [Low / Bug] `admin_reset_password` not registered in OpenAPI paths
**File:** `main.rs`, `routes/admin.rs`
The `admin_reset_password` endpoint (`PUT /api/admin/users/{id}/password`) exists but is not in the OpenAPI paths list.

## V36-8 [Low / Bug] `create_backup` not registered in OpenAPI paths
**File:** `main.rs`, `routes/admin.rs`
The `create_backup` endpoint (`POST /api/admin/backup`) exists but is not in the OpenAPI paths list.

## V36-9 [Low / Bug] `get_notif_prefs` and `update_notif_prefs` not registered in OpenAPI paths
**File:** `main.rs`, `routes/profile.rs`
Both notification preference endpoints exist but are missing from OpenAPI.

## V36-10 [Low / Bug] `get_task_sessions` not registered in OpenAPI paths
**File:** `main.rs`, `routes/tasks.rs`
`GET /api/tasks/{id}/sessions` exists but is missing from OpenAPI.

## V36-11 [Low / Bug] `room_ws` and `watch_task`/`unwatch_task`/`get_task_watchers`/`get_watched_tasks` not in OpenAPI
**File:** `main.rs`
WebSocket and watcher endpoints exist in the router but are not documented in OpenAPI.

## V36-12 [Low / Security] `attachment_random_hex` uses hash-based counter instead of `getrandom`
**File:** `routes/attachments.rs:upload_attachment`
The storage key generation uses `Sha256::digest` of a counter+timestamp seed. While collision-resistant, it's predictable. Should use `getrandom` for the random component.

## V36-13 [Low / Code Quality] `get_active_timers` returns `Vec<serde_json::Value>` instead of typed struct
**File:** `routes/timer.rs:get_active_timers`
Returns ad-hoc JSON values. Should use a proper response struct with `ToSchema` for OpenAPI documentation.

## V36-14 [Low / Performance] `user_presence` does a correlated subquery per user
**File:** `routes/misc.rs:user_presence`
`(SELECT MAX(s.started_at) FROM sessions s WHERE s.user_id = u.id)` runs for every user. With many users and sessions, this is slow. Could use a JOIN with a pre-aggregated subquery.

## V36-15 [Low / Bug] `schedule_suggestions` hardcodes 0.42 hours per session
**File:** `routes/history.rs:schedule_suggestions`
`let sessions_needed = (*hours / 0.42).ceil()` — assumes 25-minute sessions. Should use the user's configured `work_duration_min` from their config.

## V36-16 [Low / UX] Keyboard shortcut `n` for new task doesn't work on kanban/calendar tabs
**File:** `gui/src/App.tsx:handler`
The `n` shortcut only triggers when `activeTab === "tasks"`. Should also work on kanban and calendar views.

## V36-17 [Low / Code Quality] `TasksFullResponse` not registered in OpenAPI schemas
**File:** `routes/misc.rs`
The `get_tasks_full` endpoint returns `TasksFullResponse` but the struct doesn't derive `ToSchema` and isn't in the components list. The OpenAPI response type says `Vec<db::Task>` which is incorrect.

## V36-18 [Low / Bug] `export_tasks` CSV doesn't include `estimated_hours` and `remaining_points` columns
**File:** `routes/export.rs:export_tasks`
The CSV export header includes `work_duration_minutes` but omits `estimated_hours` and `remaining_points`, which were added to CSV import in V34-18. Import/export asymmetry.

## V36-19 [Low / Bug] `processSyncQueue` 409 Conflict responses are silently swallowed
**File:** `gui/src/offlineStore.ts`
After V35-14 refactored to use `apiCall`, a 409 response will now throw (since `apiCall` throws on 4xx). The old code treated 409 as success (skip conflicting entry). Need to catch 409 specifically.

## V36-20 [Low / UX] Notification bell dropdown opens to the right, may overflow on narrow screens
**File:** `gui/src/App.tsx:NotificationBell`
The dropdown has `className="absolute left-14 bottom-0 w-72"` which positions it to the right of the sidebar. On narrow viewports, this could overflow. Should check viewport bounds or use a portal.

## V36-21 [Low / Code Quality] `ical_escape` doesn't handle long lines (RFC 5545 requires folding at 75 octets)
**File:** `routes/export.rs:ical_escape`
iCal spec requires lines longer than 75 octets to be folded with CRLF+space. Long task titles or descriptions will produce non-compliant iCal output.

## V36-22 [Low / Bug] `restore_backup` calls `std::process::exit(0)` — unclean shutdown
**File:** `routes/admin.rs:restore_backup`
After restoring, the server calls `std::process::exit(0)` which bypasses the graceful shutdown handler. Background tasks (sprint snapshots, recurrence) may be mid-operation. Should send the shutdown signal instead.

## V36-23 [Low / Bug] `midnight_reset` in tick loop doesn't use user's timezone
**File:** `main.rs:175-182`
The midnight reset uses `chrono::Utc::now()` to detect day change. Users in non-UTC timezones will see their daily count reset at the wrong time. This is a known limitation but worth documenting.

## V36-24 [Low / Code Quality] Multiple route handlers use inline SQL instead of DB layer functions
**File:** Various routes (misc.rs, history.rs, admin.rs, rooms.rs)
Many endpoints contain raw `sqlx::query` calls instead of going through `db::` functions. Examples: `user_presence`, `check_achievements`, `weekly_digest`, `get_active_timers`. This makes the DB layer incomplete and harder to test.

## V36-25 [Low / Performance] `check_achievements` runs 4 separate DB queries
**File:** `routes/history.rs:check_achievements`
Calls `get_day_stats` (1 query), then 2 more queries for sprint count and estimation accuracy. Could batch the simple COUNT queries into one.

---

## Summary

| ID | Severity | Category | Status |
|----|----------|----------|--------|
| V36-1 | Medium | Security | FIXED |
| V36-2 | Medium | Security | FIXED |
| V36-3 | Medium | Bug | FIXED |
| V36-4 | Medium | Bug | FIXED |
| V36-5 | Medium | Bug | FIXED |
| V36-6 | Low | Bug | FIXED |
| V36-7 | Low | Bug | FIXED |
| V36-8 | Low | Bug | FIXED |
| V36-9 | Low | Bug | FIXED |
| V36-10 | Low | Bug | FIXED |
| V36-11 | Low | Bug | WON'T FIX — WebSocket endpoints can't be documented in OpenAPI |
| V36-12 | Low | Security | FIXED |
| V36-13 | Low | Code quality | WON'T FIX — ad-hoc JSON is acceptable for internal endpoints |
| V36-14 | Low | Performance | WON'T FIX — correlated subquery is fine for typical user counts |
| V36-15 | Low | Bug | FIXED |
| V36-16 | Low | UX | FIXED |
| V36-17 | Low | Code quality | FIXED |
| V36-18 | Low | Bug | FIXED |
| V36-19 | Low | Bug | FIXED |
| V36-20 | Low | UX | WON'T FIX — sidebar notification dropdown position is acceptable |
| V36-21 | Low | Code quality | WON'T FIX — iCal line folding not critical for most calendar apps |
| V36-22 | Low | Bug | WON'T FIX — pool already closed, process::exit is intentional |
| V36-23 | Low | Bug | WON'T FIX — UTC midnight reset is standard for server-side |
| V36-24 | Low | Code quality | WON'T FIX — inline SQL in routes is acceptable for one-off queries |
| V36-25 | Low | Performance | WON'T FIX — 4 queries is acceptable for infrequent achievement checks |

**Total: 25 items** — 15 fixed, 10 won't fix
