# BACKLOG v17 — Fresh Codebase Audit

Audit date: 2026-04-12
Codebase: ~6500 LOC backend (55 .rs), ~9200 LOC frontend (53 .ts/.tsx)
Tests: 275 backend, 154 frontend

---

## Security (6)

- [x] **S1.** Webhook secret encryption uses XOR with no IV/nonce — deterministic, trivially reversible. Should use AES-GCM or ChaCha20-Poly1305 with random nonce. (Won't-fix carried from v15 — requires crypto dep + migration. Re-evaluate.)
- [x] **S2.** `derive_key()` still falls back to `b"default-key"` when both env var and `.jwt_secret` file are missing — server should refuse to start instead of running with a hardcoded key.
- [x] **S3.** `restore_backup` overwrites live DB while pool connections are open — causes data corruption. Pool still reads/writes old file descriptors. Must either restart server automatically or refuse to restore while running.
- [x] **S4.** `extract_ip` trusts `x-real-ip`/`x-forwarded-for` unconditionally — any client can spoof IP to bypass rate limiting when not behind a reverse proxy.
- [x] **S5.** `refresh_token` has TOCTOU race — two concurrent requests with same refresh token can both pass `is_revoked` check before either revokes it, issuing two valid token pairs.
- [x] **S6.** `health` endpoint exposes `db_size_bytes`, `schema_version`, `active_timers`, heartbeat details without authentication — leaks operational info.

## Confirmed Bugs (25)

- [x] **B1.** `compare_sprints` SQL `SUM(CASE WHEN ... THEN 1 ELSE 0 END)` returns NULL for empty sprints — sqlx decode to `i64` fails with 500. Needs `COALESCE(..., 0)`.
- [x] **B2.** `update_task` missing empty-title validation — `create_task` checks `trim().is_empty()` but update only checks `len() > 500`. Can set title to empty string.
- [x] **B3.** `import_tasks_json` on rollback returns `created: N` where N > 0 — misleading since no tasks were actually created after rollback.
- [x] **B4.** `get_sprint_tasks` missing `deleted_at IS NULL` filter — soft-deleted tasks appear on sprint boards.
- [x] **B5.** `get_task_detail` recursive CTE missing `deleted_at IS NULL` — soft-deleted children appear in task detail tree.
- [x] **B6.** `search_tasks_fts` FTS5 path missing `t.deleted_at IS NULL` filter on JOIN — soft-deleted tasks appear in search results.
- [x] **B7.** `end_session` has no status check — already-completed sessions can be ended again, overwriting `ended_at` and `duration_s`.
- [x] **B8.** `parse_timestamp` silently returns `Utc::now()` on parse failure — corrupted `started_at` produces wrong duration instead of error.
- [x] **B9.** `recover_interrupted` sets `ended_at` but not `duration_s` — recovered sessions have NULL duration, breaking time stats.
- [x] **B10.** `update_profile` changes username before validating password — if password change fails, username is already committed. Should validate password first or use transaction.
- [x] **B11.** `update_config` — `theme`, `estimation_mode`, `notify_desktop`, `notify_sound` fields silently ignored for non-root users (never persisted to `user_configs`).
- [x] **B12.** App.tsx: `showShortcuts` state declared twice, shortcuts overlay rendered 3 times — duplicate modals appear.
- [x] **B13.** App.tsx: `useStore.getState().engine?.status` called during render — timer indicator dot in sidebar is stale, never re-renders on status change.
- [x] **B14.** TaskNode: `useShallow` selector includes `tasks` array — every TaskNode re-renders on any task change (O(n²)). Should use `getState()` inside handlers.
- [x] **B15.** TaskDetailView: `tasks` variable shadowed — destructured from store then re-declared as local const.
- [x] **B16.** api.ts: token refresh uses `savedServers[0]` which may not be current server — wrong refresh token used with multiple saved servers.
- [x] **B17.** SprintParts: `Column` useCallback captures stale `touchDrag` — `onTouchEnd` always sees initial `null` value.
- [x] **B18.** Timer.tsx: duplicate Space key handler — both Timer.tsx and App.tsx register Space for pause/resume, causing double-toggle.
- [x] **B19.** AuthScreen: client-side password validation only checks length, not uppercase+digit — mismatch with placeholder text and backend rules.
- [x] **B20.** `delete_user` audit_log entries deleted — destroys audit trail. Should preserve with sentinel user_id.
- [x] **B21.** `engine.tick()` drops and re-acquires states lock — race with concurrent start/stop can overwrite new session state.
- [x] **B22.** `recurrence` midnight processing uses single `today` value — if loop crosses midnight, tasks may skip a day.
- [x] **B23.** `reserved_username` list includes "root" but seed user is created as "root" — inconsistent.
- [x] **B24.** Multiple components use native `confirm()` instead of store's `showConfirm` — may not work in Tauri WebView. (Rooms.tsx, TaskDetailParts.tsx, SettingsParts.tsx)
- [x] **B25.** `get_descendant_ids` doesn't filter `deleted_at IS NULL` — soft-deleted descendants included in tree walks for delete/restore/epic snapshots.

## Business Logic (10)

- [x] **BL1.** `room_ws` broadcasts full `get_room_state` for ALL connected WebSockets on any `ChangeEvent::Rooms` — even for unrelated rooms. Thundering herd of DB queries.
- [x] **BL2.** Room creator can leave their own room — if only admin, room becomes orphaned (no one can delete or manage it).
- [x] **BL3.** Team admin can remove themselves — if last admin, team becomes unmanageable.
- [x] **BL4.** `kick_member` allows admin to kick themselves — room becomes admin-less.
- [x] **BL5.** `accept_estimate` doesn't verify room is in "revealed" state — admin can accept before reveal.
- [x] **BL6.** `VALID_ROOM_ROLES` is `["admin","voter"]` but `cast_vote` checks for `"observer"` — dead code, observer role unreachable.
- [x] **BL7.** `log_burn` (sprint) allows burns on "planning" sprints — should require `status == "active"`.
- [x] **BL8.** `export_burns` requires sprint ownership but `list_burns` has no ownership check — inconsistent authorization.
- [x] **BL9.** `get_active_webhooks` LIKE matching (`events LIKE '%task.created%'`) matches superstrings — `task.created_extra` would match.
- [x] **BL10.** `update_sprint` doesn't validate name emptiness or length — bypasses `create_sprint` validations.

## Validation Gaps (10)

- [x] **V1.** `set_recurrence` accepts any pattern string — should validate against `["daily","weekly","biweekly","monthly"]`.
- [x] **V2.** `set_recurrence` doesn't validate `next_due` date format.
- [x] **V3.** `log_burn` (sprint) no validation on `req.note` length — unbounded string to DB.
- [x] **V4.** `add_time_report` no validation on `req.description` length.
- [x] **V5.** `export_sessions` `from`/`to` query params not validated as date format.
- [x] **V6.** `get_history` `from`/`to` not validated as date format.
- [x] **V7.** `get_stats` `days` parameter has no upper bound — `?days=999999999` queries entire table.
- [x] **V8.** `create_label` no max length on label name.
- [x] **V9.** `create_template` no validation that `data` field is valid JSON.
- [x] **V10.** `add_epic_group_tasks` / `add_sprint_root_tasks` don't deduplicate task IDs — duplicate IDs cause DB errors.

## UX Improvements (8)

- [x] **UX1.** WON'T FIX — AuthScreen server URL validation accepts `javascript:` and `data:` URLs — should restrict to `http:`/`https:`.
- [x] **UX2.** WON'T FIX — Sprint retro textarea uses `defaultValue` — won't update when other users edit via SSE.
- [x] **UX3.** WON'T FIX — TaskContextMenu submenu hover zones fragile — diagonal mouse movement closes submenu (hover tunnel problem).
- [x] **UX4.** WON'T FIX — Comment edit window is 15 minutes with no visual countdown indicator.
- [x] **UX5.** WON'T FIX — Many API calls have `.catch(() => {})` — no error feedback to user (Labels, Dependencies, Recurrence, TeamManager, EpicBurndown).
- [x] **UX6.** WON'T FIX — TaskDetailView `getTaskDetail` has no `.catch()` — stays in "Loading..." forever on error.
- [x] **UX7.** WON'T FIX — Upload error in TaskAttachments silently ignored — no feedback on failure.
- [x] **UX8.** WON'T FIX — NotificationBell dropdown positioned `left-14` — may overflow on narrow viewports.

## Accessibility (8)

- [x] **A1.** WON'T FIX — TaskContextMenu doesn't auto-focus first menuitem on open — WAI-ARIA menu pattern requires it.
- [x] **A2.** WON'T FIX — Select.tsx dropdown doesn't trap focus — Tab key moves focus outside component.
- [x] **A3.** WON'T FIX — No `<h1>` on any page — heading hierarchy starts at `<h2>`.
- [x] **A4.** WON'T FIX — Color-only status indicators throughout — priority dots, status badges rely on color alone.
- [x] **A5.** WON'T FIX — Dashboard `<dl>` structure incorrect — `<dd>` before `<dt>`, `<div>` wrapper breaks dl>dt/dd structure.
- [x] **A6.** WON'T FIX — History date range inputs lack `aria-label`.
- [x] **A7.** WON'T FIX — Table view checkboxes in TaskList lack `aria-label`.
- [x] **A8.** WON'T FIX — AuthScreen password strength meter has no accessible label for screen readers.

## Performance (5)

- [x] **P1.** TaskNode `useShallow` subscribes to entire `tasks` array — O(n²) re-renders on any task change. Move `tasks` access to `getState()` inside handlers.
- [x] **P2.** `export_tasks` loads up to 50,000 tasks into memory — should use streaming response.
- [x] **P3.** `snapshot_epic_group` builds dynamic IN clause — exceeds SQLite's 999 variable limit for large epic groups.
- [x] **P4.** `get_room_state` without project loads ALL tasks of ALL members (up to 500) — expensive for large rooms.
- [x] **P5.** `update_task` auto-unblock dependents is N+1 queries — should be single SQL query.

## Infrastructure (3)

- [x] **INF1.** WON'T FIX — `admin.rs` uses blocking `std::fs` operations in async handlers (`create_backup`, `restore_backup`, `list_backups`) — blocks tokio runtime.
- [x] **INF2.** WON'T FIX — `lib.rs` CORS config uses `try_lock()` which can fail — custom origins silently dropped if lock is held at startup.
- [x] **INF3.** WON'T FIX — CSP header includes `'unsafe-inline'` for scripts and styles — weakens CSP protection.

---

**Total: 75 items** (6 security, 25 bugs, 10 business logic, 10 validation, 8 UX, 8 accessibility, 5 performance, 3 infrastructure)
