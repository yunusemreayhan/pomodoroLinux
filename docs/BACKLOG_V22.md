# BACKLOG v22 — Fresh Codebase Audit (2026-04-12)

Full audit of 58 backend .rs files (~7000 LOC), 66 frontend .ts/.tsx files (~9500 LOC), 275 backend tests, 154 frontend tests.

## Security (3 items)

- [ ] **S1.** `TaskAttachments` upload in `TaskDetailParts.tsx` uses raw `fetch()` with `Bearer ${token}` from store instead of `apiCall`/`invoke`. This bypasses Tauri's HTTP client and the automatic token refresh logic. If the token expires mid-session, uploads will silently fail with 401 instead of auto-refreshing. Same issue with `AuthImage` download.

- [ ] **S2.** `useSseConnection` creates `EventSource` directly from browser using `${url}/api/timer/sse?ticket=...`. This bypasses Tauri's HTTP client. While SSE uses ticket auth (not JWT in URL), the connection goes through the browser's network stack instead of Tauri's, which could behave differently with proxies/CORS.

- [ ] **S3.** `accept_estimate` in `rooms.rs` updates task fields (`estimated_hours` or `estimated`) based on `estimation_unit` but only handles `"points"` and `"hours"`. Rooms created with `"mandays"` or `"tshirt"` units will have `accept_estimate` store the value in the wrong field or not at all. The accepted value is passed through but the field mapping is incorrect for non-standard units.

## Bugs (5 items)

- [ ] **B1.** `list_tasks` endpoint (`GET /api/tasks`) has `_claims` parameter (unused) — it doesn't filter by user. Any authenticated user can see ALL tasks. The `export_tasks` endpoint correctly filters by `user_id` for non-root users, but `list_tasks` doesn't. This is inconsistent — either all endpoints should filter or none should (multi-tenant vs shared workspace).

- [ ] **B2.** `get_task_detail`, `get_task_sessions`, `list_comments`, `list_time_reports`, `get_task_burn_total`, `get_task_burn_users`, `get_task_votes`, `get_task_labels`, `get_recurrence`, `get_dependencies`, `list_attachments` — none check task ownership. Any authenticated user can read any task's details. This is consistent with `list_tasks` (shared workspace model) but inconsistent with `export_tasks` which filters by user.

- [ ] **B3.** `import_tasks_csv` doesn't validate `due_date` format. Invalid dates from CSV are inserted directly into the DB. The `create_task` endpoint validates `due_date` with `valid_date()`, but the CSV import bypasses this validation.

- [ ] **B4.** `bulk_update_status` doesn't fire webhooks for task updates. Single `update_task` dispatches `task.updated` webhook, but bulk status change skips webhook dispatch entirely. Teams relying on webhooks for status tracking will miss bulk updates.

- [ ] **B5.** `useRoomWebSocket` creates `WebSocket` directly from browser (same pattern as S1/S2). The `wsUrl` is constructed by replacing `http` with `ws` in `serverUrl`, but this doesn't handle `https` → `wss` correctly — `serverUrl.replace(/^http/, "ws")` would turn `https://` into `wss://` which is actually correct. However, the WebSocket still bypasses Tauri's HTTP client.

## Business Logic (3 items)

- [ ] **BL1.** `auto_archive` uses `updated_at < cutoff` to find tasks to archive. But `updated_at` changes on ANY field update (title edit, tag change, comment via task detail reload). A task completed 100 days ago but with a recent comment won't be archived. Should use a dedicated `completed_at` timestamp or check `status = 'completed'` with a separate completion date.

- [ ] **BL2.** `snapshot_sprint` counts `remaining_points` and `estimated_hours` from task fields, but these represent the original estimates, not actual burned values. The burndown chart shows estimate-based progress, not burn-log-based progress. This means manual burn entries don't affect the burndown chart — only task status changes do.

- [ ] **BL3.** `accept_estimate` auto-advance filters by `t.status != "estimated"` to find the next unestimated task. But no task ever gets status `"estimated"` through normal flow — `accept_estimate` doesn't set the accepted task's status to `"estimated"`. The filter is dead code and all tasks (including already-estimated ones) are candidates for auto-advance. The `voted_task_ids` set prevents re-voting, but the status filter is misleading.

## Validation (2 items)

- [ ] **V1.** `import_tasks_csv` doesn't validate `due_date` format from CSV data. The `create_task` endpoint validates with `valid_date()` but CSV import inserts raw values. Invalid dates like "tomorrow" or "2024-13-45" will be stored.

- [ ] **V2.** `create_room` accepts `estimation_unit` values `"mandays"` and `"tshirt"` but `accept_estimate` only handles `"points"` and `"hours"` for updating task fields. Creating a room with unsupported units will cause accepted estimates to be stored incorrectly.

## Performance (2 items)

- [ ] **P1.** `get_tasks_full` ETag computation runs a single query with 7 subqueries (`SELECT COUNT(*)` for tasks, sprint_tasks, burn_log, task_assignees, task_labels, task_attachments, plus MAX(updated_at)). While this is a single round-trip, the 7 subqueries each do a full table scan. Could be optimized with a single pass using conditional aggregation.

- [ ] **P2.** `NotificationBell` in `App.tsx` polls `/api/notifications/unread` every 30 seconds via `setInterval`, even when SSE is connected and delivering change events. The SSE `change` event could trigger a notification refresh instead of blind polling.

## Accessibility (2 items)

- [ ] **A1.** `TaskList` table view has no `<caption>` element describing the table content. Screen readers need a caption to understand the table's purpose.

- [ ] **A2.** Sprint board drag-and-drop in `SprintParts.tsx` has no keyboard alternative for moving cards between columns. Users who can't use a mouse have no way to change task status via the board view.

## Code Quality (3 items)

- [ ] **CQ1.** `RoomMember` type in frontend `types.ts` has `user_id` field missing — the interface only has `room_id`, `username`, `role`, `joined_at`. But the backend `RoomMember` struct includes `user_id`. The frontend type is incomplete, though it may not be used for user_id lookups.

- [ ] **CQ2.** `get_sprint_tasks`, `get_sprint_burndown`, `get_sprint_board`, `list_burns`, `get_burn_summary` — none verify the sprint exists before querying. Passing a non-existent sprint ID returns empty results (200 OK) instead of 404. This is technically correct (empty is valid) but inconsistent with other endpoints that return 404.

- [ ] **CQ3.** `TaskDetailView` has `ExportButton` imported and also re-exported (`export { ExportButton }`) at the bottom of the file. The re-export is unnecessary since `ExportButton` is already exported from `TaskDetailHelpers.tsx`.

---

**Total: 20 items**

Priority order: S1 (attachment upload bypasses token refresh), B3/V1 (CSV import date validation), S3/V2 (estimation unit mismatch), B4 (bulk webhooks), then remaining items.
