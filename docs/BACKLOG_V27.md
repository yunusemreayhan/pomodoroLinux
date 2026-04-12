# Post-Features Audit Backlog (V27)

Comprehensive audit of all code added during F1–F28 feature implementation.
Audited: routes/history.rs, routes/misc.rs, routes/timer.rs, routes/sprints.rs,
routes/export.rs, routes/tasks.rs, db/mod.rs, db/tasks.rs, db/types.rs, db/rooms.rs,
gui/src/offlineStore.ts, gui/src/store/store.ts, gui/src/components/Dashboard.tsx,
gui/src/components/TaskDetailView.tsx, gui/src/components/CalendarView.tsx,
gui/src/components/KanbanBoard.tsx, gui/src/App.tsx, gui/src/main.tsx, gui/public/sw.js

---

## PF1 — OpenAPI paths missing for 20+ new endpoints
**Severity:** Medium | **File:** `main.rs`
The `#[openapi(paths(...))]` macro in main.rs does not include any of the new
feature endpoints: estimation_accuracy, focus_score, list_achievements,
check_achievements, leaderboard, priority_suggestions, activity_feed,
schedule_suggestions, weekly_digest, export_ical, sprint_retro_report,
get_task_links, add_task_link, github_webhook, list_automations,
create_automation, delete_automation, toggle_automation, user_presence,
create_slack_integration, join_session, session_participants.
The `/swagger-ui` and `/api-docs/openapi.json` are incomplete.

## PF2 — OpenAPI schemas missing for new types
**Severity:** Medium | **File:** `main.rs`
New request/response types not registered in `components(schemas(...))`:
AddTaskLinkRequest, GitHubPushEvent, GitHubCommit, GitHubRepo,
CreateAutomationRuleRequest, AutomationRule, SlackIntegrationRequest,
AccuracyQuery, LeaderboardQuery, FeedQuery.

## PF3 — Unused variable `unlocked_set` in list_achievements
**Severity:** Low | **File:** `routes/history.rs:143`
`unlocked_set` is computed but never used. The function already uses `unlocked`
directly via `.iter().find()`. Remove the dead code.

## PF4 — Unused variable `claims` in get_task_time_summary
**Severity:** Low | **File:** `routes/tasks.rs:51`
`claims` should be `_claims` since it's only used for auth gating.

## PF5 — GitHub webhook has no signature verification
**Severity:** Medium-High | **File:** `routes/misc.rs` (github_webhook)
The `/api/integrations/github` endpoint accepts any POST payload without
verifying the `X-Hub-Signature-256` header. An attacker could forge webhook
payloads to create arbitrary task links. Should validate HMAC-SHA256 signature
against a stored webhook secret, or at minimum require auth.

## PF6 — Automation rules don't validate JSON fields
**Severity:** Low | **File:** `routes/misc.rs` (create_automation)
`condition_json` and `action_json` are stored as raw strings without validating
they are valid JSON. Should parse with `serde_json::from_str::<Value>()` before
storing to prevent garbage data.

## PF7 — F9 activity_feed `since` parameter not validated as datetime
**Severity:** Low | **File:** `routes/history.rs` (activity_feed)
The `since` query param defaults to `"2000-01-01T00:00:00"` but any string is
accepted. SQLite will silently compare strings, so garbage input won't crash but
will return unexpected results. Should validate format or return 400.

## PF8 — Service worker caches API responses with auth tokens
**Severity:** Medium | **File:** `gui/public/sw.js`
The SW caches all GET `/api/*` responses including authenticated data. If the
user logs out and another user logs in on the same browser, stale cached data
from the previous user could be served during offline fallback. Should clear
the API cache on logout, or scope cached API responses by user.

## PF9 — offlineStore.ts opens/closes DB on every operation
**Severity:** Low | **File:** `gui/src/offlineStore.ts`
Every function calls `openDB()` and `db.close()`. This is inefficient for
`cacheTasksOffline` which does N puts. Should keep a singleton connection or
at least not close after each call. Not a bug, but wasteful.

## PF10 — Checklist toggle fires updateTask on every click without debounce
**Severity:** Low | **File:** `gui/src/components/TaskDetailView.tsx`
`DescriptionWithChecklists.toggle()` calls `updateTask()` immediately on each
checkbox click. Rapid clicking could fire multiple concurrent PUT requests with
stale `description` values, causing race conditions. Should debounce or use
optimistic local state.

## PF11 — KanbanBoard drop handler doesn't prevent self-drop
**Severity:** Low | **File:** `gui/src/components/KanbanBoard.tsx`
The `onDrop` handler checks `task.status === colId` to skip no-op drops, but
the status mapping (`done` → `completed`, `estimated` → `backlog`) means
dropping a "done" task on the "completed" column would fire an unnecessary
`updateTask(id, { status: "completed" })` even though it's already done.

## PF12 — CalendarView doesn't handle deleted tasks
**Severity:** Low | **File:** `gui/src/components/CalendarView.tsx`
The `tasksByDate` memo filters `t.status !== "archived"` but doesn't filter
`t.deleted_at`. Soft-deleted tasks with due dates would still appear on the
calendar. Should add `&& !t.deleted_at`.

## PF13 — F8 FocusScore widget makes API call without token check
**Severity:** Low | **File:** `gui/src/components/Dashboard.tsx`
The `FocusScore` and `Achievements` components fire API calls in `useEffect([])`
without checking if the user is authenticated. If rendered before login, they'll
make unauthorized requests that fail silently. Not harmful but wasteful.

## PF14 — F22 Achievements widget fires POST on every Dashboard render
**Severity:** Medium | **File:** `gui/src/components/Dashboard.tsx`
`Achievements` calls `POST /api/achievements/check` every time the Dashboard
mounts. This is a write operation that should be called sparingly (e.g., after
completing a session), not on every tab switch to Dashboard.

## PF15 — F11 join_session doesn't prevent joining own session
**Severity:** Low | **File:** `routes/timer.rs` (join_session)
A user can join their own active session as a "participant", which is
semantically meaningless. Should check `session.user_id != claims.user_id`.

## PF16 — F14 Slack integration URL validation too permissive
**Severity:** Low | **File:** `routes/misc.rs` (create_slack_integration)
Accepts any URL starting with `https://hooks.slack.com/` or
`https://discord.com/api/webhooks/`. Should also validate URL length and
reject URLs with query params or fragments that could be used for SSRF
when the webhook is eventually called.

## PF17 — F20 weekly_digest is POST but has no side effects
**Severity:** Low | **File:** `routes/history.rs` (weekly_digest)
`POST /api/reports/weekly-digest` is a read-only operation that generates a
report. Should be GET for proper HTTP semantics and cacheability.

---

## Summary

| ID | Severity | Category | Status |
|----|----------|----------|--------|
| PF1 | Medium | OpenAPI completeness | TODO |
| PF2 | Medium | OpenAPI completeness | TODO |
| PF3 | Low | Dead code | TODO |
| PF4 | Low | Dead code | TODO |
| PF5 | Medium-High | Security | TODO |
| PF6 | Low | Validation | TODO |
| PF7 | Low | Validation | TODO |
| PF8 | Medium | Security | TODO |
| PF9 | Low | Performance | TODO |
| PF10 | Low | UX/Race condition | TODO |
| PF11 | Low | Logic | TODO |
| PF12 | Low | Logic | TODO |
| PF13 | Low | Wasted requests | TODO |
| PF14 | Medium | Wasted writes | TODO |
| PF15 | Low | Logic | TODO |
| PF16 | Low | Validation | TODO |
| PF17 | Low | HTTP semantics | TODO |

**Total: 17 items** (1 medium-high, 3 medium, 13 low)
