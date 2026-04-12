# Flow: Root User Creates a Task

## Actor
Authenticated user with role `root`.

## Steps

Identical to [user-creates-task.md](user-creates-task.md). No special root behavior on creation.

1. Root sends `POST /api/tasks` with Bearer token.
2. Validation runs (same rules as normal user).
3. Task created with `user_id = root's user_id`.
4. Audit log + webhook + SSE broadcast.
5. Returns `201 Created`.

## Authorization
- No role check on task creation — root follows the same path as any user.
- The root user becomes the owner.

## Difference from Normal User
None on creation. The difference is in subsequent operations — root can update/delete **any** task via `is_owner_or_root()`.
