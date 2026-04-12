# BUG: Any User Can Log Burns on Any Sprint

## Severity
Low–Medium

## Location
`crates/pomodoro-daemon/src/routes/burns.rs` — `log_burn`

## Description
The `log_burn` endpoint validates that:
- The sprint exists and is not completed
- The task exists and is not deleted
- The task belongs to the sprint

But it does **not** check:
- Whether the user is the sprint owner
- Whether the user is assigned to the task
- Whether the user has any relationship to the sprint at all

## Current Behavior
```
User A creates Sprint 1 with Task 1.
User B (no relation to sprint or task) sends POST /api/sprints/1/burn {"task_id": 1, "hours": 8}.
→ 201 Created — burn logged under User B's name.
```

## Expected Behavior
Only users who are assigned to the task, or the sprint owner, or root should be able to log burns.

## Fix
Add a check that the user is either the sprint owner, assigned to the task, or root:
```rust
if claims.role != "root" && sprint.created_by_id != claims.user_id {
    let assignees = db::list_assignees(&engine.pool, req.task_id).await.map_err(internal)?;
    if !assignees.contains(&claims.username) {
        return Err(err(StatusCode::FORBIDDEN, "Not assigned to this task"));
    }
}
```

## Impact
Low in a trusted team, but allows data pollution — anyone can inflate/deflate burndown charts.
