# Flow: User Creates a Sprint

## Actor
Any authenticated user (normal or root).

## Steps

1. User sends `POST /api/sprints` with:
   ```json
   {
     "name": "Sprint 1",
     "project": "MyProject",
     "goal": "Deliver feature X",
     "start_date": "2026-04-14",
     "end_date": "2026-04-28",
     "capacity_hours": 80
   }
   ```
2. Route handler `create_sprint` runs:
   - Validates name (non-empty, max 200 chars).
   - Validates goal (max 1000 chars).
   - Validates dates (YYYY-MM-DD format, end ≥ start).
   - Validates capacity_hours (0–10000).
   - Calls `db::create_sprint` with `claims.user_id` as `created_by_id`.
3. Sprint created with status `planning`.
4. Audit log + webhook (`sprint.created`) + SSE broadcast.
5. Returns `201 Created`.

## Sprint Lifecycle

```
planning → active → completed
                  ↘ carryover → new sprint (planning)
```

### Start Sprint
- `POST /api/sprints/{id}/start`
- **Owner or root only** (`get_owned_sprint` checks `is_owner_or_root`).
- Must be in `planning` status.
- Takes a burndown snapshot.

### Complete Sprint
- `POST /api/sprints/{id}/complete`
- **Owner or root only**.
- Must be in `active` status.
- Takes a final burndown snapshot.

### Carry Over
- `POST /api/sprints/{id}/carryover`
- **Owner or root only**.
- Must be `completed`.
- Creates a new sprint with incomplete tasks.

## Sprint Task Management

### Add Tasks
- `POST /api/sprints/{id}/tasks` with `{"task_ids": [1, 2, 3]}`
- **Owner or root only**.
- Validates tasks exist and are not soft-deleted.
- Deduplicates task IDs.

### Remove Task
- `DELETE /api/sprints/{id}/tasks/{task_id}`
- **Owner or root only**.

## Authorization Summary

| Action | Sprint Owner | Root | Other Users |
|---|---|---|---|
| Create sprint | ✅ | ✅ | ✅ |
| View sprint | ✅ | ✅ | ✅ |
| Update sprint | ✅ | ✅ | ❌ |
| Delete sprint | ✅ | ✅ | ❌ |
| Start/Complete | ✅ | ✅ | ❌ |
| Add/Remove tasks | ✅ | ✅ | ❌ |
| Log burns | ✅ | ✅ | ✅ (any user) |
| View burndown | ✅ | ✅ | ✅ |

## ⚠️ BUG: Any User Can Log Burns on Any Sprint

`log_burn` does not check sprint ownership or membership. Any authenticated user can log burn entries on any sprint's tasks. See `backlog/burn-log-no-auth.md`.
