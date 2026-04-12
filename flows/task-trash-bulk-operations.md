# Flow: Task Soft Delete, Trash & Restore

## Soft Delete (`DELETE /api/tasks/{id}`)
1. Checks `is_owner_or_root`.
2. `db::delete_task` sets `deleted_at = now()` (soft delete).
3. Cascades to subtasks (children also soft-deleted).
4. Audit log + webhook + SSE broadcast.

## Trash (`GET /api/tasks/trash`)
- Root: sees all deleted tasks.
- Normal user: sees only own deleted tasks (`user_id` filter).

## Restore (`POST /api/tasks/{id}/restore`)
1. Checks `is_owner_or_root`.
2. Sets `deleted_at = NULL`.
3. SSE broadcast.

## Auto-Archive (daily background task)
- Completed tasks older than `auto_archive_days` (from config) → status set to `archived`.
- Only affects non-deleted tasks.

## Bulk Status Update (`PUT /api/tasks/bulk-status`)
- Accepts `{task_ids: [...], status: "..."}`.
- Root: can update any tasks.
- Normal user: batch ownership check — all tasks must be owned by the user.
- Max 500 tasks per request.

## Reorder (`POST /api/tasks/reorder`)
- Accepts `{orders: [[id, sort_order], ...]}`.
- Root: can reorder any tasks.
- Normal user: batch ownership check.
- Max 500 items.
