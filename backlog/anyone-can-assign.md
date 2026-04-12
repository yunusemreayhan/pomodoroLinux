# BUG: Anyone Can Assign Anyone to Any Task

## Severity
Medium

## Location
`crates/pomodoro-daemon/src/routes/assignees.rs` — `add_assignee`

## Description
The `POST /api/tasks/{id}/assignees` endpoint has no authorization check. The `_claims` parameter is unused. Any authenticated user can assign any user to any task, regardless of task ownership.

## Current Behavior
```
User A creates Task 1.
User B (not owner, not root) sends POST /api/tasks/1/assignees {"username": "C"}.
→ 200 OK — User C is now assigned to Task 1.
```

## Expected Behavior
Only the task owner or root should be able to assign users to a task. Alternatively, users should be able to assign themselves (self-assign) but not others.

## Fix
Add ownership check in `add_assignee`:
```rust
let task = db::get_task(&engine.pool, id).await.map_err(|_| err(StatusCode::NOT_FOUND, "Task not found"))?;
if !is_owner_or_root(task.user_id, &claims) {
    // Allow self-assignment
    let uid = db::get_user_id_by_username(&engine.pool, &req.username).await...;
    if uid != claims.user_id {
        return Err(err(StatusCode::FORBIDDEN, "Not owner"));
    }
}
```

## Impact
Low risk in a trusted team environment, but violates principle of least privilege.
