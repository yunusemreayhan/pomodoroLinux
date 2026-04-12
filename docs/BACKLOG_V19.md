# BACKLOG v19 — Fresh Codebase Audit (2026-04-12)

Full audit of 56 backend .rs files (6547 LOC), 53 frontend .ts/.tsx files (9282 LOC), 275 backend tests, 154 frontend tests.

## Security (5 items)

- [ ] **S1.** `api_rate_limit` middleware uses `std::sync::Mutex` (blocking) inside async context — can block the tokio runtime under high contention. Replace with `parking_lot::Mutex` or `tokio::sync::Mutex`.
- [ ] **S2.** `RateLimiter` uses `Vec<Instant>` per IP — O(n) cleanup per request. Under sustained load from one IP, the vec grows unbounded within the window. Use a sliding window counter (two counters per window) instead.
- [ ] **S3.** `Sidebar` sends partial config `{ theme: th }` via `apiCall("PUT", "/api/config", { theme: th })` — backend `update_config` expects a full `Config` struct. This overwrites all other config fields with serde defaults (e.g., resets `work_duration_min` to 25). Should use PATCH semantics or merge with current config.
- [ ] **S4.** Webhook secret encryption uses XOR with a derived key — this is not a real encryption scheme (no IV, no authentication, trivially reversible if key is known). Should use AES-GCM or ChaCha20-Poly1305 via the `aead` crate.
- [ ] **S5.** `download_attachment` reads entire file into memory via `tokio::fs::read` — for large files (up to 10MB), this holds the full content in RAM. Use `tokio_util::io::ReaderStream` for streaming response.

## Bugs (12 items)

- [ ] **B1.** `Sidebar` theme toggle calls `apiCall("PUT", "/api/config", { theme: th })` which sends a partial Config — backend deserializes it as a full Config with defaults, overwriting user's timer durations, daily goal, etc. Every theme toggle resets all settings.
- [ ] **B2.** `useSseConnection` creates a new EventSource on every `token` change — if the token is refreshed (via `tryRefreshToken`), the old SSE connection is closed and a new one opened, causing a brief gap where timer ticks are missed.
- [ ] **B3.** `Rooms.tsx` has duplicate `import { useStore }` — line 5 imports from `../store/store` and line 6 also imports `useStore` from `../store/store`. This is a duplicate import that bundlers handle but is messy.
- [ ] **B4.** `TeamManager` calls `apiCall("GET", "/api/users")` which returns `string[]` (usernames only), but the component expects `{ id: number; username: string }[]` — the user search/add feature is broken because `u.id` is undefined.
- [ ] **B5.** `import_tasks_csv` doesn't handle the new `description` column added to CSV export in v18 — export now has 12 columns but import still expects 4 columns (title, priority, estimated, project). Round-trip is broken.
- [ ] **B6.** `duplicate_task` route handler doesn't copy `work_duration_minutes` — duplicated tasks lose their custom timer duration.
- [ ] **B7.** `carryover_sprint` copies `start_date`/`end_date` from the completed sprint — but these are the OLD sprint's dates. The carry-over sprint should have no dates (or shifted dates), not the same dates as the completed sprint.
- [ ] **B8.** `ErrorBoundary` calls `useI18n.getState()` inside `render()` of a class component — this works but is unconventional and may break if zustand changes its API. Should use a wrapper or context.
- [ ] **B9.** `allUsers` state in `TeamManager` is typed as `{ id: number; username: string }[]` but `/api/users` returns `string[]` — TypeScript doesn't catch this because `apiCall` uses a generic type parameter that trusts the caller.
- [ ] **B10.** `change_password` (PUT /api/auth/password) route exists in the router but the handler validates `current_password` — if the user provides wrong current password, the error message says "Current password is incorrect" but the status is 403 (FORBIDDEN) instead of 401 (UNAUTHORIZED).
- [ ] **B11.** `restore_backup` closes the pool but the server continues running with a dead pool — all subsequent requests will fail with connection errors until restart. The response says "Restart the server" but there's no mechanism to trigger it.
- [ ] **B12.** `isDescendantOf` in `TaskNode` drag-and-drop walks the parent chain via `tasks` array lookup — for deep trees (50+ levels), this is O(depth × n) per drag operation. Should use a Map for O(depth) lookup.

## Business Logic (6 items)

- [ ] **BL1.** `add_assignee` route allows task owner to assign anyone, but `remove_assignee` also requires task ownership — an assigned user cannot unassign themselves from a task they don't own.
- [ ] **BL2.** `delete_team` is root-only but `create_team` is available to any user — a non-root user can create teams but only root can delete them, leaving orphaned teams if the creator leaves.
- [ ] **BL3.** `update_sprint` rejects `status` field changes ("Use /start or /complete endpoints") but doesn't prevent setting status via the `status` field in the request — the check returns an error, which is correct, but the error message could be clearer about which endpoints to use.
- [ ] **BL4.** `auto_archive` task loop runs daily but doesn't check if the task has active timer sessions — archiving a task that's currently being timed could cause confusion.
- [ ] **BL5.** `accept_estimate` for "tshirt" unit stores the numeric value (1,2,3,5,8) as `estimated` — but the frontend displays T-shirt labels (XS,S,M,L,XL). The stored value loses the T-shirt semantics.
- [ ] **BL6.** `carryover_sprint` doesn't check if any of the incomplete tasks are already in another active sprint — could result in a task being in two active sprints simultaneously.

## Validation (4 items)

- [ ] **V1.** `update_profile` allows changing username to any string including empty — `validate_username` is called but if it only checks length, usernames with special characters (spaces, unicode) could be created.
- [ ] **V2.** `create_task` doesn't validate `title` length — unbounded string stored in DB. Should cap at 500 chars like `import_tasks_json` does.
- [ ] **V3.** `update_sprint` doesn't validate `project` length on update — only `create_sprint` validates it.
- [ ] **V4.** `add_time_report` allows `hours` up to 24.0 per entry but doesn't limit total hours per day per user — a user could log 100+ hours in a single day across multiple entries.

## UX Improvements (6 items)

- [ ] **UX1.** `Dashboard` component loads stats and sprints independently but doesn't show sprint progress or upcoming due dates — missed opportunity for a useful overview widget.
- [ ] **UX2.** `History` component loads sessions but doesn't display `task_path` breadcrumbs even though the API returns them — the data is fetched but not rendered.
- [ ] **UX3.** No visual indicator for tasks with unresolved dependencies in the task list — users can't see at a glance which tasks are blocked (only visible in sprint board).
- [ ] **UX4.** No way to edit a label name or color after creation — only create and delete are supported.
- [ ] **UX5.** No way to edit a webhook URL or events after creation — only create and delete.
- [ ] **UX6.** `TaskContextMenu` "Move up/Move down" swaps sort_order values — but if two tasks have the same sort_order (common after import), the swap is a no-op.

## Accessibility (3 items)

- [ ] **A1.** `NotificationBell` dropdown has no focus trap — Tab key escapes the dropdown to the page behind it. Should trap focus within the dialog.
- [ ] **A2.** `CsvImport` drag-and-drop zone label is not focusable via keyboard — the `<label>` wraps a hidden input but the label itself doesn't have `tabIndex` so keyboard users can't discover it without Tab-navigating to the hidden input.
- [ ] **A3.** `Rooms` "Show closed" toggle button doesn't have `aria-pressed` attribute — screen readers can't determine the toggle state.

## Performance (3 items)

- [ ] **P1.** `get_task_detail` recursive CTE fetches all descendants then batch-loads comments and sessions for each — for deeply nested trees with many comments, this generates N+1 queries. Should batch-load comments for all descendant IDs in one query.
- [ ] **P2.** `Sidebar` calls `apiCall("GET", "/api/me/teams")` on mount but the result is stored in local state — if the user navigates away and back, teams are re-fetched. Should cache in the store.
- [ ] **P3.** `loadTasks` compares tasks with `some((t, i) => t.id !== prev[i]?.id || t.updated_at !== prev[i]?.updated_at)` — O(n) comparison on every load. The ETag from `/api/tasks/full` already handles this at the HTTP level (304 Not Modified), but the client-side comparison still runs.

## Code Quality (4 items)

- [ ] **CQ1.** `Rooms.tsx` has duplicate `import { useStore } from "../store/store"` on consecutive lines — should be deduplicated.
- [ ] **CQ2.** `api_rate_limit` uses `std::sync::Mutex` which is a blocking mutex — should use `parking_lot::Mutex` for better performance in async context (no poisoning, faster).
- [ ] **CQ3.** `webhook.rs` `dispatch` function spawns a tokio task per webhook event — if many events fire rapidly, this creates many concurrent HTTP requests. Should use a bounded channel/queue.
- [ ] **CQ4.** Multiple route handlers have inline SQL queries that could be extracted to `db/` layer functions — e.g., `create_room` has `SELECT COUNT(*) FROM rooms WHERE creator_id = ?` inline.

---

**Total: 43 items** — S:5, B:12, BL:6, V:4, UX:6, A:3, P:3, CQ:4
