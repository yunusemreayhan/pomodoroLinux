# Flow: Normal User Is Assigned to a Task They Did Not Create

## Actor
Authenticated user with role `user`, being assigned to another user's task.

## Steps

### Assigning
1. Any authenticated user sends `POST /api/tasks/{id}/assignees` with `{"username": "target_user"}`.
2. Route handler `add_assignee` runs:
   - Looks up target user by username.
   - Calls `db::add_assignee(task_id, user_id)`.
   - **No ownership check** — `_claims` is unused.
3. Returns `200 OK`.

### What the assigned user can do
- **View the task**: Yes (all tasks are visible to everyone).
- **Update the task**: **NO** — `update_task` checks `is_owner_or_root(task.user_id, &claims)`. Being assigned does not grant write access.
- **Delete the task**: **NO** — same ownership check.
- **Comment on the task**: **YES** — `add_comment` only checks task exists, not ownership.
- **Start a timer on the task**: **YES** — timer routes don't check task ownership.
- **Log burns on the task**: **YES** — burn logging checks sprint membership, not task ownership.

### Removing assignment
- `DELETE /api/tasks/{id}/assignees/{username}` — **requires task ownership or root**. The assigned user cannot unassign themselves.

## ⚠️ BUG: Anyone Can Assign Anyone
The `add_assignee` endpoint has **no authorization check**. Any authenticated user can assign any user to any task, even tasks they don't own. See `backlog/anyone-can-assign.md`.

## ⚠️ BUG: Assignees Cannot Update Tasks
An assigned user cannot modify the task (change status, update description, etc.). This breaks the typical workflow where an assigned developer needs to move a task to "in_progress" or "completed". See `backlog/assignee-cannot-update.md`.

## ⚠️ BUG: Assigned User Cannot Unassign Themselves
`remove_assignee` requires task ownership. An assigned user who wants to decline/leave the task cannot remove their own assignment. See `backlog/assignee-cannot-unassign-self.md`.
