# Flow: Normal User Creates a Task

## Actor
Authenticated user with role `user`.

## Steps

1. User sends `POST /api/tasks` with Bearer token.
2. `Claims` extractor validates JWT, checks token not revoked, verifies user exists in DB.
3. Route handler `create_task` runs:
   - Validates title (non-empty, max 500 chars).
   - Validates description (max 10000), project (max 200), tags (max 500).
   - Validates priority (1–5, default 3), estimated (≥0, default 1).
   - Validates estimated_hours (≥0), due_date (YYYY-MM-DD format).
   - Calls `db::create_task` with `claims.user_id` as owner.
4. Task is inserted into `tasks` table with `user_id = claims.user_id`.
5. Audit log entry created (`action: "create"`, `entity: "task"`).
6. Webhook dispatched (`task.created`).
7. SSE `ChangeEvent::Tasks` broadcast to all connected clients.
8. Returns `201 Created` with the task JSON.

## Authorization
- Any authenticated user can create tasks. No role check.
- The creating user becomes the task owner (`user_id`).

## Ownership Model
- `tasks.user_id` = the creator/owner.
- Only the owner (or root) can update/delete the task later.
