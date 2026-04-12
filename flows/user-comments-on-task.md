# Flow: Normal User Comments on a Task

## Actor
Authenticated user with role `user`, commenting on any task (own or others').

## Steps

### Adding a Comment
1. User sends `POST /api/tasks/{id}/comments` with `{"content": "...", "session_id": null}`.
2. Route handler `add_comment` runs:
   - Validates content is non-empty and ≤10000 chars.
   - Verifies task exists (`db::get_task`).
   - **No ownership check** — any user can comment on any task.
   - Inserts comment with `user_id = claims.user_id`.
3. SSE `ChangeEvent::Tasks` broadcast.
4. Returns `201 Created` with comment JSON.

### Editing a Comment
1. User sends `PUT /api/comments/{id}` with `{"content": "..."}`.
2. Checks `is_owner_or_root(comment.user_id, &claims)` — only comment author (or root) can edit.
3. **15-minute edit window** — rejects if comment is older than 15 minutes.
4. Returns updated comment.

### Deleting a Comment
1. User sends `DELETE /api/comments/{id}`.
2. Checks `is_owner_or_root(comment.user_id, &claims)` — only comment author (or root) can delete.
3. Returns `204 No Content`.

## Authorization Summary

| Action | Own comment | Other's comment |
|---|---|---|
| Create | ✅ on any task | ✅ on any task |
| Edit | ✅ (within 15 min) | ❌ `403 Not owner` |
| Delete | ✅ | ❌ `403 Not owner` |

## Notes
- Comments are linked to `task_id` and optionally `session_id`.
- The comment model supports threaded replies via `parent_id` in the DB schema (if present).
- No notification is sent to the task owner when someone comments — the SSE broadcast updates all connected clients.
