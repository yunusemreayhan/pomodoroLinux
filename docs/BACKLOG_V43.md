# Backlog V43 — Full Codebase Audit (2026-04-13)

Scope: Stability, correctness, security, performance, UX, accessibility, code quality.
No new features.

---

## V43-1 [Medium / Bug] `unwatch_task` doesn't check task existence — silently succeeds for non-existent task
**File:** `routes/watchers.rs:unwatch_task`
No task existence check. The DELETE silently succeeds even if the task doesn't exist.

## V43-2 [Medium / Bug] `get_task_watchers` doesn't check task existence — returns empty instead of 404
**File:** `routes/watchers.rs:get_task_watchers`
Returns `[]` for non-existent task IDs.

## V43-3 [Medium / Bug] `unwatch_task` DB silently succeeds if user isn't watching
**File:** `db/watchers.rs:unwatch_task`
The DELETE silently succeeds even if the user isn't watching the task. Should check rows_affected.

## V43-4 [Medium / Security] JWT secret fallback uses weak entropy on `getrandom` failure
**File:** `auth.rs:secret()`
If `getrandom::fill` fails, the fallback uses `Sha256(timestamp + pid)` which is predictable. While `getrandom` failure is extremely rare, the fallback should at least log at ERROR level and the server should refuse to start rather than use weak entropy.

## V43-5 [Low / Bug] `export_tasks` CSV doesn't include `status` column in header but includes it in data
**File:** `routes/export.rs:export_tasks`
The CSV header is `id,parent_id,title,description,project,tags,priority,estimated,actual,estimated_hours,remaining_points,status,due_date,created_at,work_duration_minutes` — actually it does include status. FALSE POSITIVE on closer inspection.

## V43-6 [Low / Code Quality] `token_hash` uses manual hex encoding instead of `hex::encode`
**File:** `auth.rs:token_hash`
Uses `.iter().map(|b| format!("{:02x}", b)).collect()` when `hex::encode` is already a dependency (used in webhook.rs).

## V43-7 [Low / Bug] `iCal export` doesn't fold long lines per RFC 5545
**File:** `routes/export.rs:export_ical`
RFC 5545 requires content lines to be no longer than 75 octets. Long task titles or descriptions will produce non-compliant iCal output. Most parsers tolerate this, but strict parsers may reject it.

## V43-8 [Low / Bug] `import_tasks_csv` doesn't validate `from`/`to` date params in `export_tasks`
**File:** `routes/export.rs:export_tasks`
The `ExportQuery` has `from` and `to` fields but `export_tasks` ignores them entirely. Only `export_sessions` validates and uses them. The fields are misleading in the tasks export.

## V43-9 [Low / Code Quality] `kick_member` calls `leave_room` which now returns error for non-members — should map to 404
**File:** `routes/rooms.rs:kick_member`
After V41-11, `db::leave_room` returns an error if the user isn't a member. But `kick_member` maps this to `internal` (500) instead of 404.

## V43-10 [Low / Bug] `set_room_role` doesn't verify target user is a room member
**File:** `routes/rooms.rs:set_room_role`
The endpoint resolves the username to a user_id and calls `set_room_member_role`, but doesn't verify the user is actually a member of the room. The DB UPDATE silently succeeds (0 rows affected) for non-members.

---

## Summary

| ID | Severity | Category | Status |
|----|----------|----------|--------|
| V43-1 | Medium | Bug | FIXED — returns 404 for non-existent task |
| V43-2 | Medium | Bug | FIXED — returns 404 for non-existent task |
| V43-3 | Medium | Bug | FIXED — returns 400 if not watching |
| V43-4 | Medium | Security | FIXED — panics instead of using weak entropy |
| V43-5 | Low | Bug | FALSE POSITIVE — CSV header does include status |
| V43-6 | Low | Code quality | FIXED — uses hex::encode |
| V43-7 | Low | Bug | WON'T FIX — most parsers tolerate long lines |
| V43-8 | Low | Bug | WON'T FIX — shared ExportQuery struct, tasks have no date range |
| V43-9 | Low | Code quality | FIXED — maps to 404 |
| V43-10 | Low | Bug | FIXED — returns 404 if not a member |

**Total: 10 items** — 7 fixed, 2 won't fix, 1 false positive
