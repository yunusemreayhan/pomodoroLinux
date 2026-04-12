# Flow: Normal User Changes Estimation of a Task

## Actor
Authenticated user with role `user`, attempting to change estimation fields on a task.

## Estimation Fields
- `estimated` — story points (integer)
- `estimated_hours` — hours (float)
- `remaining_points` — remaining effort (float)

## Steps

1. User sends `PUT /api/tasks/{id}` with `{"estimated": 5}` (or `estimated_hours`, `remaining_points`).
2. Route handler `update_task` runs:
   - Fetches task from DB.
   - **Checks `is_owner_or_root(task.user_id, &claims)`** — only the task owner or root can update.
   - If user is the owner: validates and applies the change.
   - If user is NOT the owner: returns `403 Not owner`.

## ⚠️ BUG: Assignees Cannot Change Estimation

A user assigned to a task cannot update its estimation. This is problematic because:

1. In planning poker (rooms), the team votes on estimates, and the room admin accepts the value — this writes directly to the task via `accept_estimate`. This works.
2. But outside of rooms, if a developer is assigned a task and realizes the estimate is wrong, they cannot correct it. Only the task creator can.

See `backlog/assignee-cannot-update.md` (same root cause as the general assignee update issue).

## How Estimation Changes Actually Happen

| Method | Who can do it | Notes |
|---|---|---|
| `PUT /api/tasks/{id}` | Owner or root only | Direct field update |
| Room `accept_estimate` | Room admin or root | Writes voted value to task |
| Burn logging | Any sprint member | Updates `remaining_points` indirectly via burn entries |

## Recommendation
Assignees should be allowed to update estimation fields (at minimum `remaining_points`) on tasks assigned to them.
