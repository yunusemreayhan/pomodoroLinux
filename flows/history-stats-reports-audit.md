# Flow: History, Stats, Reports & Audit

## Session History (`GET /api/history`)
- Params: `from`, `to`, `user_id`.
- Root: can filter by any user_id, or see all.
- Normal user: **forced to own sessions only** (overrides `user_id` param).
- Returns sessions with task path breadcrumbs.

## Day Stats (`GET /api/stats?days=N`)
- Returns daily aggregates: completed sessions, total duration.
- Root: all users combined.
- Normal user: own stats only.

## User Hours Report (`GET /api/reports/user-hours`)
- **Root only.**
- Params: `from`, `to`.
- Returns per-user: username, total hours, session count.

## Task Time Summary (`GET /api/tasks/{id}/time-summary`)
- Any user. No ownership check.
- Returns per-user breakdown of hours spent on a specific task.

## Audit Log (`GET /api/audit`)
- Any authenticated user can view the full audit log.
- Filterable by `entity_type`, `entity_id`.
- Paginated (default 100, max 500 per page).
- Records: user_id, action, entity_type, entity_id, detail, timestamp.

## ⚠️ Note: Audit Log Visible to All Users
The audit log contains all actions by all users (task creates, deletes, role changes, etc.). Any authenticated user can read it. This may expose sensitive admin actions to normal users.
