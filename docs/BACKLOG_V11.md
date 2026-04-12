# BACKLOG v11

Full codebase audit of 5765 LOC backend (Rust/axum/SQLite) and 8392 LOC frontend (React/TypeScript/Tauri). 219 backend tests, 154 frontend tests. Analysis date: 2026-04-12.

---

## Bugs (B1–B12)

**B1: Timer start ignores per-task work_duration_minutes**
F9 added `work_duration_minutes` to the Task struct and DB, but `engine.rs:start()` always uses `config.work_duration_min * 60` for work phase duration. It never reads the task's `work_duration_minutes` override. Fix: if `task_id` is provided and the task has `work_duration_minutes`, use it instead of the config default.

**B2: Dashboard `today` computed once on render, stale after midnight**
`Dashboard.tsx` computes `const today = new Date().toISOString().slice(0, 10)` once. If the app stays open past midnight, the dashboard shows yesterday's data. Fix: recompute `today` on an interval or use a reactive time hook.

**B3: Sprint carry-over doesn't check if user owns the sprint**
`carryover_sprint` checks `is_owner_or_root` but uses `get_owned_sprint` helper inconsistently — it calls `db::get_sprint` directly then checks ownership manually, duplicating the pattern Q5 was supposed to eliminate.

**B4: `export_room_history` doesn't verify room membership**
Any authenticated user can export any room's vote history via `GET /api/rooms/{id}/export`. Should verify the caller is a room member or root.

**B5: `update_session_note` route not registered in OpenAPI**
The `update_session_note` handler in `tasks.rs` lacks a `#[utoipa::path]` annotation, so it doesn't appear in Swagger UI or the generated OpenAPI spec.

**B6: Dashboard uses `BarChart3` icon for both dashboard and history tabs**
Both tabs use the same `BarChart3` icon in the TABS array, making them visually indistinguishable in the sidebar.

**B7: `import_tasks_json` recursive function uses `Box::pin` but doesn't limit depth**
The JSON import recursion has no depth limit. A deeply nested JSON payload (1000+ levels) could stack overflow. Add a max depth parameter (e.g., 20).

**B8: `carryover_sprint` and `export_room_history` not registered in OpenAPI**
These endpoints lack `#[utoipa::path]` annotations and don't appear in the Swagger spec.

**B9: Table view in TaskList doesn't support bulk selection**
When `viewMode === "table"`, the bulk selection checkboxes and toolbar are hidden because they're inside the tree view branch of the ternary.

**B10: `get_tasks_full` response doesn't include `work_duration_minutes` in frontend types**
The `Task` interface in `types.ts` is missing `work_duration_minutes?: number | null`, so the frontend silently drops this field.

**B11: Sprint `capacity_hours` not in frontend Sprint type**
The `Sprint` interface in `types.ts` is missing `capacity_hours?: number | null`, so the frontend can't display or edit it.

**B12: `watch_task` / `unwatch_task` route handlers have unused `_claims` / `claims` inconsistency**
`unwatch_task` takes `claims` but doesn't use it for ownership check (any user can unwatch any task). This is correct behavior but the parameter should be `_claims` for consistency, or the handler should verify the user is unwatching themselves.

---

## Security (S1–S5)

**S1: No rate limiting on WebSocket ticket creation**
`POST /api/timer/ticket` creates SSE/WS tickets but isn't rate-limited beyond the global API rate limiter. A malicious user could exhaust the ticket pool (HashMap) by creating thousands of tickets. Add per-user ticket limit (e.g., max 5 active tickets).

**S2: Attachment download doesn't verify task ownership**
`download_attachment` only checks that the attachment exists, not that the caller has access to the parent task. Any authenticated user can download any attachment by ID. Fix: verify the caller owns the task, is an assignee, or is root.

**S3: `bulk_update_status` SQL injection via dynamic placeholder construction**
While the current code binds values safely, the `format!("... IN ({}) ...", ph)` pattern for building placeholder strings is fragile. If `task_ids` contained non-i64 values (impossible with current deserialization but risky if types change), it could be exploited. Consider using a fixed-size batch approach or sqlx's array binding.

**S4: Webhook secret encryption uses XOR — weak cipher**
`db/webhooks.rs` encrypts webhook secrets with XOR against an HMAC-derived key. XOR encryption is trivially reversible if the key is compromised. Consider using AES-GCM via the `aes-gcm` crate for proper authenticated encryption.

**S5: `create_backup` path traversal via timestamp manipulation**
While the backup path is constructed from `chrono::Utc::now().format()`, the `VACUUM INTO` command uses string interpolation. If the system clock were manipulated to produce a path with `../`, it could write outside the backup directory. Add path canonicalization check.

---

## Validation (V1–V6)

**V1: `update_sprint` doesn't validate date ordering on update**
V4 added date validation to `create_sprint`, but `update_sprint` doesn't check that the new `end_date >= start_date` when either date is changed.

**V2: `add_sprint_tasks` doesn't check for duplicate task IDs in request**
If the same task_id appears multiple times in the `task_ids` array, it could create duplicate sprint_task entries (depending on DB constraints).

**V3: `cast_vote` allows voting on tasks not in the room**
The handler checks room status and membership but doesn't verify that `current_task_id` belongs to the room's task set.

**V4: `work_duration_minutes` has no upper bound validation**
The `UpdateTaskRequest` accepts any `Option<Option<i64>>` for `work_duration_minutes`. A value of 999999 would create a timer running for ~694 days. Add bounds (e.g., 1-480 minutes).

**V5: `reorder_tasks` doesn't validate sort_order values**
The `ReorderRequest` accepts arbitrary `(i64, i64)` tuples. Negative or extremely large sort_order values could cause unexpected ordering behavior.

**V6: `import_tasks_json` doesn't validate title/description lengths**
The JSON import creates tasks without checking title length (max 500) or description length (max 10000), bypassing the validation in `create_task` route.

---

## Tests (T1–T10)

**T1: Test sprint carry-over endpoint**
Test `POST /api/sprints/{id}/carryover` — verify new sprint created with incomplete tasks, completed sprint required, empty incomplete list rejected.

**T2: Test task watcher endpoints**
Test `POST/DELETE /api/tasks/{id}/watch`, `GET /api/tasks/{id}/watchers`, `GET /api/watched` — verify watch/unwatch cycle, watcher list, watched tasks list.

**T3: Test JSON task import**
Test `POST /api/import/tasks/json` — verify nested tree creation, max 500 limit, empty title rejected.

**T4: Test session note update**
Test `PUT /api/sessions/{id}/note` — verify note updated, non-owner rejected, max length enforced.

**T5: Test room export endpoint**
Test `GET /api/rooms/{id}/export` — verify JSON response with vote history, Content-Disposition header.

**T6: Test per-task work duration override**
Test that `work_duration_minutes` is persisted via `PUT /api/tasks/{id}` and returned in task detail.

**T7: Test sprint capacity_hours**
Test that `capacity_hours` is accepted on create/update and returned in sprint detail.

**T8: Test auto-archive background task**
Test that completed tasks older than 90 days get archived status (requires time manipulation or direct DB setup).

**T9: Test dependency cycle detection**
Test that `POST /api/tasks/{id}/dependencies` with `depends_on_id` creating a cycle is rejected (A→B→A).

**T10: Test webhook URL length validation**
Test that `POST /api/webhooks` with URL > 2000 chars returns 400.

---

## Performance (P1–P4)

**P1: `get_room_state` fetches all votes for all tasks on every call**
`db/rooms.rs:get_room_state` runs a query for every task in the room to build `vote_history`. For rooms with 50+ tasks, this is O(n) queries. Fix: batch-fetch all votes in one query grouped by task_id.

**P2: `list_tasks_paged` builds team scope descendant set on every request**
When `team_id` is set, `get_descendant_ids` runs a recursive CTE on every paginated request. Cache the result per team_id with a short TTL (e.g., 30s) or invalidate on task tree changes.

**P3: SSE timer handler re-fetches `get_state` on every watch channel notification**
The SSE handler calls `engine.get_state(user_id)` which queries the DB for `daily_completed` on every tick (once per second). Cache `daily_completed` in the engine state and only refresh on session completion.

**P4: `get_tasks_full` serializes entire response on every request even with ETag match**
The ETag check happens before data fetch, but the response is always serialized. Consider caching the serialized response body alongside the ETag.

---

## Features (F1–F12)

**F1: Task search with full-text search (FTS5)**
SQLite supports FTS5 for fast full-text search. Currently, task search uses `LIKE '%query%'` which is O(n). Add an FTS5 virtual table for title/description/tags and use it for search queries.

**F2: Keyboard shortcuts help overlay**
No discoverable way to learn keyboard shortcuts. Add a `?` shortcut that shows a modal listing all available shortcuts (n=new task, s=cycle status, 0-7=switch tabs, etc.).

**F3: Sprint velocity trend line**
The velocity chart shows bars per sprint but no trend line. Add a moving average line to show velocity trend over time.

**F4: Task time tracking summary per user**
No way to see total hours logged per user across all tasks. Add a `/api/reports/user-hours` endpoint and a report view showing hours by user for a date range.

**F5: Bulk task import from clipboard (paste)**
Allow pasting a newline-separated list of task titles directly into the task list input to create multiple tasks at once.

**F6: Sprint retrospective template**
When completing a sprint, offer a structured retro template (What went well? What didn't? Action items?) instead of a free-text `retro_notes` field.

**F7: Task activity timeline**
Show a unified timeline of all changes to a task (status changes, comments, time reports, assignee changes) using the audit log data.

**F8: Configurable auto-archive threshold**
F1 hardcodes 90 days for auto-archive. Make this configurable via the config endpoint (e.g., `auto_archive_days: Option<u32>`).

**F9: Room estimation timer**
Add an optional countdown timer per voting round (e.g., 2 minutes) to prevent estimation sessions from dragging on.

**F10: Task quick filters (saved views)**
Allow saving filter combinations (status + project + assignee + priority) as named views that can be quickly switched between.

**F11: Export dashboard as PDF/image**
Add a button to export the dashboard view as a shareable image or PDF for standup meetings.

**F12: WebSocket heartbeat monitoring in frontend**
The WebSocket hook reconnects on close but doesn't detect zombie connections (open but not receiving data). Add a heartbeat check — if no message received in 60s, force reconnect.

---

## UX (U1–U7)

**U1: No loading skeleton for task list**
When tasks are loading, the list shows nothing. Add a skeleton/shimmer placeholder to prevent layout shift.

**U2: Sprint board drag-drop has no mobile touch support**
The sprint board uses HTML5 drag-and-drop which doesn't work on touch devices. Add touch event handlers or use a library like `@dnd-kit`.

**U3: Timer doesn't show which task is selected when idle**
When the timer is idle, there's no indication of which task will be used when starting. Show the selected task name below the timer circle.

**U4: Dashboard doesn't show weekly/monthly trends**
The dashboard only shows today's stats. Add a small sparkline or mini-chart showing the last 7 days of focus time.

**U5: No confirmation before deleting a sprint with tasks**
Deleting a sprint with tasks assigned silently removes the sprint. Add a confirmation dialog showing how many tasks will be unlinked.

**U6: Estimation room doesn't show who hasn't voted yet**
During voting, the UI shows who voted but not who is still pending. Highlight pending voters to encourage participation.

**U7: Table view columns not sortable by click**
The U3 table view shows data but column headers aren't clickable for sorting. Add click-to-sort on each column header.

---

## Code Quality (Q1–Q5)

**Q1: `routes/sprints.rs` still has 3 raw `db::get_sprint` + ownership check patterns**
Q5 added `get_owned_sprint` but `start_sprint`, `complete_sprint`, and `carryover_sprint` still use the manual pattern. Migrate them.

**Q2: Frontend `Task` type doesn't match backend after v10 changes**
Backend `Task` now has `work_duration_minutes: Option<i64>` but the frontend `Task` interface doesn't include it. This causes silent data loss on round-trips.

**Q3: `routes/watchers.rs` has unused `claims` parameter warnings**
`add_task_dependency` and `remove_task_dependency` take `claims` but don't use it (no ownership check on dependencies). Either add ownership validation or prefix with `_`.

**Q4: Duplicate `use super::*;` at file boundaries in concatenated route files**
Several route files start with `use super::*;` which is fine individually, but the concatenated output shows redundant imports. Not a real issue but indicates the module structure could be cleaner.

**Q5: `Dashboard.tsx` doesn't use `useMemo` for `activeCount` and `completedToday`**
These are computed on every render with `.filter()`. Wrap in `useMemo` for consistency with `overdue` and `recentlyUpdated`.

---

## Documentation (D1–D3)

**D1: API changelog missing v10 entries**
`docs/API_CHANGELOG.md` doesn't document the v10 endpoints: `/api/import/tasks/json`, `/api/sprints/{id}/carryover`, `/api/sessions/{id}/note`, `/api/rooms/{id}/export`, `/api/tasks/{id}/watch`, `/api/tasks/{id}/watchers`, `/api/watched`.

**D2: ARCHITECTURE.md doesn't mention background tasks**
The architecture doc describes the system overview but doesn't list the 6 background tasks (tick, snapshot, recurrence, auto-archive, attachment cleanup, due reminders) or their intervals.

**D3: No CONTRIBUTING.md or development setup guide**
No documentation on how to set up the development environment, run tests, or contribute. Add a guide covering: Rust toolchain, Node.js setup, `cargo test`, `npm test`, `tsc --noEmit`.

---

## DevOps (O1–O3)

**O1: No health check for background task liveness**
The `/api/health` endpoint reports heartbeat timestamps but doesn't flag tasks as unhealthy if their heartbeat is stale (e.g., >2x their interval). Add a `healthy: bool` field per task.

**O2: No database size monitoring**
The health endpoint doesn't report database file size or table row counts. Add `db_size_bytes` and key table counts to help operators monitor growth.

**O3: Backup endpoint doesn't support restore**
`POST /api/admin/backup` creates backups but there's no restore endpoint. Add `POST /api/admin/restore` that accepts a backup filename and replaces the current database (with safety checks).

---

## Accessibility (A1–A3)

**A1: Table view lacks proper `<th scope>` attributes**
The U3 table view uses `<th>` elements without `scope="col"`, making it harder for screen readers to associate headers with data cells.

**A2: Dashboard stat cards lack semantic structure**
The dashboard stats use generic `<div>` elements. Use `<dl>/<dt>/<dd>` (description list) for better semantic meaning.

**A3: Sprint board columns lack keyboard drag-and-drop**
The sprint board supports mouse drag-and-drop and arrow key navigation, but there's no way to move tasks between columns using only the keyboard (e.g., Ctrl+Arrow).

---

## Cleanup (C1–C3)

**C1: Dead code — `_claims` in `export_room_history`**
The handler takes `_claims: Claims` but doesn't use it for authorization. Either add membership check (see B4) or remove the auth requirement.

**C2: Unused `creator_id` field on Room struct**
`Room` has `creator_id` but the frontend `Room` interface uses `creator` (username string). The `creator_id` is only used server-side. Consider removing it from the serialized response.

**C3: `TaskLabel` struct in `db/labels.rs` duplicates `Label` fields**
`TaskLabel` has `id`, `name`, `color` which are the same as `Label` minus `created_at`. Consider using `Label` with `#[serde(skip)]` on `created_at` or a flattened struct.

---

**Total: 65 items** (12 bugs, 5 security, 6 validation, 10 tests, 4 performance, 12 features, 7 UX, 5 code quality, 3 documentation, 3 devops, 3 accessibility, 3 cleanup)
