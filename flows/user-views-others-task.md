# Flow: Normal User Views a Task They Did Not Create

## Actor
Authenticated user with role `user`, viewing a task owned by another user.

## Steps

1. User sends `GET /api/tasks/{id}` with Bearer token.
2. `Claims` extractor validates JWT.
3. Route handler `get_task_detail` runs:
   - Fetches task detail from DB.
   - **No ownership check** — `_claims` is unused.
4. Returns `200 OK` with full task detail (title, description, comments, sessions, assignees).

## Also applies to
- `GET /api/tasks` — lists **all** tasks, no user filtering.
- `GET /api/tasks/full` — returns all tasks, sprints, burns, assignees.
- `GET /api/tasks/{id}/comments` — no ownership check.
- `GET /api/tasks/{id}/sessions` — no ownership check.
- `GET /api/tasks/{id}/time-summary` — no ownership check.
- `GET /api/tasks/search` — searches all tasks.

## Authorization
- **All tasks are visible to all authenticated users regardless of ownership.**
- This is by design for a collaborative team tool.

## Notes
- There is no concept of "private tasks" — every user sees everything.
- The `list_tasks` endpoint supports filtering by `team_id`, `assignee`, `project`, etc., but these are optional filters, not access controls.
