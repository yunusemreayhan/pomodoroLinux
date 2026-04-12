# BUG: Assignees Cannot Update Tasks They Are Assigned To

## Severity
High — breaks core workflow.

## Location
`crates/pomodoro-daemon/src/routes/tasks.rs` — `update_task`

## Description
The `update_task` handler checks `is_owner_or_root(task.user_id, &claims)`. Being assigned to a task grants no write access. An assigned developer cannot:
- Change task status (e.g., move to `in_progress` or `completed`)
- Update description or notes
- Change estimation
- Set due date

## Current Behavior
```
User A creates Task 1, assigns User B.
User B sends PUT /api/tasks/1 {"status": "in_progress"}.
→ 403 Forbidden "Not owner"
```

## Expected Behavior
Assignees should be able to update tasks assigned to them, at minimum:
- Change `status`
- Update `description`
- Update `remaining_points`

## Fix
Extend the ownership check in `update_task` to include assignees:
```rust
let is_assignee = db::is_assignee(&engine.pool, id, claims.user_id).await.unwrap_or(false);
if !is_owner_or_root(task.user_id, &claims) && !is_assignee {
    return Err(err(StatusCode::FORBIDDEN, "Not owner or assignee"));
}
```

Also apply to `delete_task` (debatable) and `restore_task`.

## Impact
High — this is the most common multi-user workflow. Without this fix, only the task creator can move tasks through the board.
