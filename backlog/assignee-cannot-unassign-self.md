# BUG: Assigned User Cannot Unassign Themselves

## Severity
Medium

## Location
`crates/pomodoro-daemon/src/routes/assignees.rs` — `remove_assignee`

## Description
The `remove_assignee` handler checks `is_owner_or_root(task.user_id, &claims)`. An assigned user who wants to decline or leave a task cannot remove their own assignment.

## Current Behavior
```
User A creates Task 1, assigns User B.
User B sends DELETE /api/tasks/1/assignees/B.
→ 403 Forbidden "Not owner"
```

## Expected Behavior
A user should always be able to remove their own assignment from a task.

## Fix
```rust
let task = db::get_task(&engine.pool, id).await.map_err(internal)?;
let target_uid = db::get_user_id_by_username(&engine.pool, &username).await...;
// Allow self-unassign or owner/root
if target_uid != claims.user_id && !is_owner_or_root(task.user_id, &claims) {
    return Err(err(StatusCode::FORBIDDEN, "Not owner"));
}
```

## Impact
Medium — users get stuck on tasks they can't leave without asking the task creator.
