# BACKLOG v21 — Fresh Codebase Audit (2026-04-12)

Full audit of 56 backend .rs files (~6600 LOC), 53 frontend .ts/.tsx files (~9300 LOC), 275 backend tests, 154 frontend tests.

## Security (4 items)

- [ ] **S1.** `change_password` in `auth_routes.rs` does not invalidate user cache or old tokens after password change. Only `admin_reset_password` calls `invalidate_user_cache`. User-initiated password change should also invalidate cache so old tokens are rejected via `password_changed_at` check.

- [ ] **S2.** `login` in `auth_routes.rs` rehashes password on cost upgrade (`current_cost < 12`) but this triggers `update_user_password` which now sets `password_changed_at` — immediately invalidating the token just issued. The rehash path should bypass `password_changed_at` or use a separate DB function.

- [ ] **S3.** `create_backup` in `admin.rs` uses `format!("VACUUM INTO '{}'", path_str)` — string interpolation into SQL. While path characters are validated, this is still a SQL injection vector if `POMODORO_DATA_DIR` contains crafted values. Use parameterized approach or `sqlx::query` with bind.

- [ ] **S4.** `restore_backup` copies a file over the live DB after `pool.close()`, but the pool is still referenced by all route handlers via `Arc<Engine>`. Subsequent requests will fail with pool-closed errors until restart. Should return 503 after restore or trigger graceful shutdown.

## Bugs (7 items)

- [ ] **B1.** `ctxUsers` in `TaskContextMenu` receives `string[]` from `/api/users` but the endpoint now returns `{id, username}[]` objects (changed in v19 B4). The context menu assignee list will show `[object Object]` instead of usernames. Fix: map to extract `.username` or use a typed fetch.

- [ ] **B2.** `toast` ID in `store.ts` uses `Date.now() * 1000 + Math.floor(Math.random() * 1000)` — same overflow pattern fixed in `CommentSection` (v20 B3). Should use modulo like the comment fix.

- [ ] **B3.** `TaskDetailView` references `detail.time_reports` and `detail.comments` in the markdown export (`ExportButton`) but `TaskDetail` struct only has `comments`, `sessions`, and `children` — no `time_reports` field. The export will silently skip time reports. Fix: fetch burns separately or add to TaskDetail.

- [ ] **B4.** `update_session_note` route handler sends `{ notes: noteText }` from Timer.tsx but the request body type `UpdateSessionNoteRequest` expects `{ note: String }` (singular). The note will never be saved. Fix: align field name.

- [ ] **B5.** `duplicate_task` copies labels but not dependencies, assignees, or recurrence. If a user duplicates a task expecting a full copy, these are silently lost.

- [ ] **B6.** `get_descendant_ids` is called in `delete_task`, `restore_task`, `get_sprint_scope`, `get_team_scope`, and `list_tasks_paged` (team filter) but its implementation is not shown in the read files. If it uses recursive CTE, it should have a depth limit to prevent runaway queries on deeply nested trees.

- [ ] **B7.** `TaskDetailHelpers.tsx` has `ProgressBar` function that appears to be split — the function signature and body are separated by `EstimateVsActual`. This is a syntax error that TypeScript somehow tolerates (likely the closing brace is misplaced). Verify the component renders correctly.

## Business Logic (4 items)

- [ ] **BL1.** `change_password` in `auth_routes.rs` doesn't call `invalidate_user_cache` — old tokens remain valid for up to 60 seconds (cache TTL). Combined with S1, this means a user who changes their password to lock out a compromised session has a 60-second window where the old token still works.

- [ ] **BL2.** `auto_archive_days` config field is validated on save (min 1 via `.max(1)`) but `0` is documented as "disabled" in the archive loop (`if days == 0 { continue; }`). The config validation doesn't allow setting 0 to disable. Fix: allow 0 in validation or remove the disable check.

- [ ] **BL3.** Sprint `complete_sprint` doesn't check if there are incomplete tasks. A sprint can be completed with 0% done tasks, which may be unintentional. Consider adding a warning or requiring confirmation.

- [ ] **BL4.** `carryover_sprint` creates a new sprint but doesn't copy `retro_notes` from the completed sprint. The retro notes from the previous sprint are lost in the carry-over context.

## Validation (3 items)

- [ ] **V1.** `auto_archive_days` has no upper bound validation in `update_config`. A user could set it to `u32::MAX` (4 billion days). Add a reasonable max (e.g., 3650 = 10 years).

- [ ] **V2.** `add_sprint_root_tasks` doesn't validate the task IDs exist before inserting. If a non-existent task ID is passed, it silently inserts a dangling reference. The sprint tasks endpoint validates but roots don't.

- [ ] **V3.** `export_sessions` doesn't validate `from`/`to` date format. Invalid dates are passed directly to the SQL query. While SQLite handles this gracefully (returns no results), it should return 400 for malformed dates.

## UX Improvements (3 items)

- [ ] **UX1.** `NotificationBell` polls `/api/notifications/unread` every 30 seconds via `setInterval`. This should use SSE change events (already available via `ChangeEvent`) instead of polling, reducing unnecessary API calls.

- [ ] **UX2.** `TaskContextMenu` fetches sprints and users on every right-click if cache is older than 5 seconds (`ctxCacheTime`). The cache is module-level but not shared across TaskNode instances — each node has its own `ctxSprints`/`ctxUsers` state. The cache time check works but the data is duplicated per node.

- [ ] **UX3.** `Dashboard` component's `TeamActivity` widget polls `/api/timer/active` every 15 seconds. When the dashboard tab is not active, this still fires. Should pause polling when tab is not visible.

## Performance (3 items)

- [ ] **P1.** `get_room_state` fetches up to 500 votes, then iterates them multiple times to build `vote_history`. For rooms with many historical votes, this is O(votes × unique_tasks). Consider using a SQL GROUP BY to build history server-side.

- [ ] **P2.** `bulk_update_status` auto-unblock logic does N × M individual `get_task` calls (N = completed tasks, M = their dependents' dependencies). For large bulk operations, this could be hundreds of DB queries. Consider batching the dependency check.

- [ ] **P3.** `list_tasks_paged` with team filter calls `get_descendant_ids` which may return thousands of IDs, all bound individually as SQL parameters. SQLite has a default limit of 999 bind parameters. Large team scopes could hit this limit.

## Accessibility (2 items)

- [ ] **A1.** `TaskList` table view (`viewMode === "table"`) doesn't have `aria-sort` on sortable column headers. Screen readers can't tell which column is sorted or the sort direction.

- [ ] **A2.** `EstimationRoomView` countdown overlay uses `role="alert"` but the countdown numbers change rapidly (3, 2, 1). This will cause screen readers to announce each number. Consider using `aria-live="off"` during countdown and only announcing the final "revealing" state.

## Code Quality (2 items)

- [ ] **CQ1.** `TaskDetailView` export button references `detail.time_reports` and `detail.comments` with `?.length` but `TaskDetail` type doesn't have `time_reports`. TypeScript should catch this — verify if there's a type mismatch or if the field exists at runtime but not in the type definition.

- [ ] **CQ2.** `ctxUsers` type mismatch: `TaskContextMenu` declares `ctxUsers: string[]` but `TaskNode` fetches from `/api/users` which returns `{id, username}[]`. The prop type and fetch result are inconsistent. This is the same root cause as B1.

---

**Total: 28 items**

Priority order: S1, S2, B1, B4, then remaining security, bugs, validation, then everything else.
