# Backlog V46 — Full Codebase Audit (2026-04-13)

Scope: Stability, correctness, security, performance, UX, accessibility, code quality.
No new features.

---

## V46-1 [Medium / Bug] `get_team` returns 500 instead of 404 for non-existent team
**File:** `routes/teams.rs:get_team`
`db::get_team_detail(...).map_err(internal)` — maps "not found" to 500.

## V46-2 [Medium / Bug] `delete_team` returns 500 instead of 404 for non-existent team
**File:** `routes/teams.rs:delete_team`
`db::delete_team(...).map_err(internal)` — the `is_team_admin` check also returns 500 if team doesn't exist.

## V46-3 [Medium / Bug] `remove_team_member` silently succeeds if user isn't a member
**File:** `db/teams.rs:remove_team_member`
The DELETE silently succeeds. Should check rows_affected.

## V46-4 [Medium / Bug] `remove_team_root_task` silently succeeds if task isn't a root task
**File:** `db/teams.rs:remove_team_root_task`
Same pattern — DELETE silently succeeds.

## V46-5 [Low / Bug] `get_team_scope` returns 500 instead of 404 for non-existent team
**File:** `routes/teams.rs:get_team_scope`
`db::get_team_detail(...).map_err(internal)` — maps "not found" to 500.

## V46-6 [Low / Bug] `get_recurrence` doesn't check task existence — returns null for non-existent task
**File:** `routes/recurrence.rs:get_recurrence`
Returns `null` for non-existent task, which is ambiguous with "task exists but has no recurrence".

## V46-7 [Low / Bug] `remove_recurrence` silently succeeds if task has no recurrence
**File:** `db/recurrence.rs:remove_recurrence`
The DELETE silently succeeds. Should check rows_affected.

## V46-8 [Low / Bug] `add_team_member` doesn't verify target user exists
**File:** `routes/teams.rs:add_team_member`
`req.user_id` is passed directly to the DB. If the user doesn't exist, it fails with a FK error mapped to 500 instead of 404.

---

## Summary

| ID | Severity | Category | Status |
|----|----------|----------|--------|
| V46-1 | Medium | Bug | FIXED — returns 404 |
| V46-2 | Medium | Bug | FIXED — checks existence first |
| V46-3 | Medium | Bug | FIXED — returns 404 if not a member |
| V46-4 | Medium | Bug | FIXED — returns 404 if not a root task |
| V46-5 | Low | Bug | FIXED — returns 404 |
| V46-6 | Low | Bug | FIXED — checks task existence |
| V46-7 | Low | Bug | FIXED — returns 404 if no recurrence |
| V46-8 | Low | Bug | FIXED — verifies user exists |

**Total: 8 items** — 8 fixed
