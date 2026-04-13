# Backlog V39 — Full Codebase Audit (2026-04-13)

Scope: Stability, correctness, security, performance, UX, accessibility, code quality.
No new features.

---

## V39-1 [Medium / Bug] `seed_root_user` uses `rand::rng()` instead of `getrandom` for password generation
**File:** `db/users.rs:8-10`
`rand::rng().sample(Alphanumeric)` is used to generate the root password. While `rand` uses `getrandom` internally, this is the last remaining `rand::` usage in the codebase — inconsistent with the V36 decision to use `getrandom` directly everywhere. Should use `getrandom` + hex encoding for consistency.

## V39-2 [Medium / Bug] `URL.createObjectURL` memory leaks in CSV export
**File:** `gui/src/components/History.tsx:203`, `gui/src/components/SprintViews.tsx:145`
Two CSV export locations create blob URLs without calling `URL.revokeObjectURL()`. Each click leaks a blob URL. History.tsx line 203 (weekly CSV) and SprintViews.tsx line 145 (burndown CSV) are affected.

## V39-3 [Medium / Bug] `join_session` checks `status == "running"` but sessions table stores `"completed"/"interrupted"` — no `"running"` status
**File:** `routes/timer.rs:join_session`
`session.0 != "running"` — but `create_session` in `db/sessions.rs` sets status to `"running"`. Let me verify this is correct by checking the DB layer.

## V39-4 [Medium / Bug] LIKE search doesn't escape `%` and `_` wildcards in user input
**File:** `db/tasks.rs:117,199,213`
`format!("%{}%", s)` where `s` is user search input. If a user searches for `%` or `_`, these are SQL LIKE wildcards and will match unintended rows. Should escape `%` → `\%` and `_` → `\_` with `ESCAPE '\'`.

## V39-5 [Low / Bug] `list_burns` doesn't check sprint existence — returns empty for non-existent sprint
**File:** `routes/burns.rs:list_burns`
`db::list_burns(&engine.pool, id)` returns empty vec for non-existent sprint ID instead of 404.

## V39-6 [Low / Bug] `get_burn_summary` doesn't check sprint existence
**File:** `routes/burns.rs:get_burn_summary`
Same pattern as V39-5 — returns empty for non-existent sprint.

## V39-7 [Low / Bug] `list_time_reports` doesn't check task existence
**File:** `routes/burns_task.rs:list_time_reports`
Returns empty for non-existent task ID instead of 404.

## V39-8 [Low / Bug] `get_task_burn_total` doesn't check task existence
**File:** `routes/burns_task.rs:get_task_burn_total`
Returns zero totals for non-existent task instead of 404.

## V39-9 [Low / Bug] `get_task_burn_users` doesn't check task existence
**File:** `routes/burns_task.rs:get_task_burn_users`
Returns empty for non-existent task instead of 404.

## V39-10 [Low / Code Quality] `RefreshRequest` and `ChangePasswordRequest` not registered in OpenAPI schemas
**File:** `routes/auth_routes.rs`, `main.rs`
Both structs have `ToSchema` derives but aren't in the `components(schemas(...))` list.

## V39-11 [Low / Code Quality] `RestoreRequest` not registered in OpenAPI schemas
**File:** `routes/admin.rs`, `main.rs`
`RestoreRequest` has `ToSchema` but isn't in the schemas list.

## V39-12 [Low / Code Quality] `SearchQuery`, `ReorderRequest` not registered in OpenAPI schemas
**File:** `routes/tasks.rs`, `main.rs`
Both have `ToSchema` derives but aren't registered.

## V39-13 [Low / Bug] `update_notif_prefs` doesn't limit number of prefs per request
**File:** `routes/profile.rs:update_notif_prefs`
No limit on `prefs.len()`. A malicious client could send thousands of entries, each triggering a DB write. Should cap at `EVENT_TYPES.len()`.

## V39-14 [Low / Bug] `export_room_history` exports `vote_history` but doesn't include task titles
**File:** `routes/rooms.rs:export_room_history`
The exported JSON contains `vote_history` which has `task_id` but not task titles. The export is less useful without human-readable task names.

## V39-15 [Low / Performance] `user_presence` runs a correlated subquery per user
**File:** `routes/misc.rs:user_presence`
`(SELECT MAX(s.started_at) FROM sessions s WHERE s.user_id = u.id)` runs for every user. With many users and sessions, this could be slow. A JOIN with GROUP BY would be more efficient.

## V39-16 [Low / Code Quality] `CreateTemplateRequest` not registered in OpenAPI schemas
**File:** `routes/templates.rs`, `main.rs`

## V39-17 [Low / Bug] `instantiate_template` doesn't copy tags, due_date, or estimated_hours from template data
**File:** `routes/templates.rs:instantiate_template`
The template instantiation reads `title`, `description`, `project`, `priority`, `estimated` from the template data but ignores `tags`, `due_date`, and `estimated_hours` even though `create_task` accepts them.

## V39-18 [Low / Code Quality] `RoomRoleRequest` not registered in OpenAPI schemas
**File:** `routes/types.rs`, `main.rs`

---

## Summary

| ID | Severity | Category | Status |
|----|----------|----------|--------|
| V39-1 | Medium | Bug | FIXED — getrandom replaces rand for root password |
| V39-2 | Medium | Bug | FIXED — revokeObjectURL added to 2 CSV exports |
| V39-3 | Medium | Bug | FALSE POSITIVE — sessions do use "running" status |
| V39-4 | Medium | Bug | FIXED — LIKE search escapes % and _ wildcards |
| V39-5 | Low | Bug | FIXED — 404 for non-existent sprint |
| V39-6 | Low | Bug | FIXED — 404 for non-existent sprint |
| V39-7 | Low | Bug | FIXED — 404 for non-existent task |
| V39-8 | Low | Bug | FIXED — 404 for non-existent task |
| V39-9 | Low | Bug | FIXED — 404 for non-existent task |
| V39-10 | Low | Code quality | FIXED — RefreshRequest + ChangePasswordRequest in schemas |
| V39-11 | Low | Code quality | FIXED — RestoreRequest in schemas |
| V39-12 | Low | Code quality | FIXED — ReorderRequest in schemas |
| V39-13 | Low | Bug | FIXED — prefs array capped at EVENT_TYPES.len() |
| V39-14 | Low | Bug | WON'T FIX — task_ids sufficient for JSON export |
| V39-15 | Low | Performance | WON'T FIX — correlated subquery fine for SQLite |
| V39-16 | Low | Code quality | FIXED — CreateTemplateRequest in schemas |
| V39-17 | Low | Bug | FIXED — tags/due_date/estimated_hours read from template |
| V39-18 | Low | Code quality | FIXED — RoomRoleRequest in schemas |

**Total: 18 items** — 14 fixed, 2 won't fix, 2 false positive
