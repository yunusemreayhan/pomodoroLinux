# Flow: Import / Export

## Export Tasks
`GET /api/export/tasks?format=json|csv`
- Root: exports all tasks.
- Normal user: exports only own tasks (`user_id` filter).
- CSV includes: id, parent_id, title, project, tags, priority, estimated, actual, status, due_date, created_at.
- CSV injection prevention: formula-triggering characters prefixed.

## Export Sessions
`GET /api/export/sessions?format=csv|json&from=YYYY-MM-DD&to=YYYY-MM-DD`
- Root: all sessions. Normal user: own sessions only.
- Includes task path (breadcrumb).

## Export Burns
`GET /api/export/burns/{sprint_id}`
- Any authenticated user (no ownership check on sprint).
- CSV format with burn entries.

## Import Tasks (JSON)
`POST /api/import/tasks/json`
- Accepts JSON array of task objects.
- Creates tasks owned by the importing user.
- Returns created tasks.

## Import Tasks (CSV)
`POST /api/import/tasks`
- Accepts CSV with headers matching task fields.
- Creates tasks owned by the importing user.

## Authorization Summary
| Operation | Normal User | Root |
|---|---|---|
| Export tasks | Own tasks only | All tasks |
| Export sessions | Own sessions only | All sessions |
| Export burns | All (no filter) | All |
| Import tasks | Creates as own | Creates as own |

## ⚠️ Note: Export Burns Has No Access Control
Any user can export burn data for any sprint, including sprints they have no relation to.
