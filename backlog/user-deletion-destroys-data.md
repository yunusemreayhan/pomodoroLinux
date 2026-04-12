# BUG: User Deletion Destroys Comments and Burn Logs

## Severity
Medium — data loss.

## Location
`crates/pomodoro-daemon/src/db/users.rs` — `delete_user`

## Description
When a user is deleted, their comments and burn_log entries are hard-deleted (`DELETE FROM comments WHERE user_id = ?`, `DELETE FROM burn_log WHERE user_id = ?`). Meanwhile, tasks and sessions are reassigned to the first root user.

## Impact
- Comments on tasks disappear — other users lose context.
- Burn log entries disappear — sprint burndown charts become inaccurate.
- Audit log entries are also deleted — traceability lost.

## Fix
Reassign instead of delete:
```rust
sqlx::query("UPDATE comments SET user_id = (SELECT id FROM users WHERE role = 'root' LIMIT 1) WHERE user_id = ?")
    .bind(id).execute(pool).await?;
sqlx::query("UPDATE burn_log SET user_id = (SELECT id FROM users WHERE role = 'root' LIMIT 1) WHERE user_id = ?")
    .bind(id).execute(pool).await?;
```

Or soft-delete users instead of hard-deleting them.
