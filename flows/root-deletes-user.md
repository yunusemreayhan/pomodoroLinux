# Flow: Root Deletes a User

## Actor
Authenticated user with role `root`.

## Steps

1. Root sends `DELETE /api/admin/users/{id}`.
2. Checks `claims.role == "root"` → `403` if not.
3. Checks `claims.user_id != id` → `400 "Cannot delete yourself"`.
4. `db::delete_user` runs:
   - Fetches user, checks if role is `root`.
   - If root: counts root users → `"Cannot delete the last root user"` if ≤1.
   - **Cascading cleanup** (in order):
     - Delete burn_log entries.
     - Delete comments.
     - Delete task_assignees.
     - Delete room_members.
     - Delete room_votes.
     - Delete audit_log entries.
     - Delete webhooks.
     - **Reassign** sessions → first root user.
     - **Reassign** tasks → first root user.
     - **Reassign** sprint_tasks.added_by_id → first root user.
     - **Reassign** rooms.creator_id → first root user.
     - **Reassign** sprints.created_by_id → first root user.
     - Delete user row.
5. `auth::invalidate_user_cache(id)` → removes from 60s existence cache.
6. Returns `204 No Content`.

## What Happens to the Deleted User's Session
- Their access token is **not revoked** — it remains valid until expiry (up to 2h).
- However, the `Claims` extractor checks user existence in DB (with 60s cache).
- After cache invalidation, the next request will fail with `401`.
- The deleted user's GUI will get 401 → refresh fails (user not found) → auto-logout.

## Data Preservation
- Tasks and sessions are **reassigned** to the first root user, not deleted.
- Comments and burn logs are **deleted** (data loss).

## ⚠️ BUG: Comments and Burns Deleted on User Deletion

When a user is deleted, their comments and burn_log entries are hard-deleted. This destroys historical data. Comments on tasks and burn entries in sprints disappear, which can break burndown charts and task history.

See `backlog/user-deletion-destroys-data.md`.
