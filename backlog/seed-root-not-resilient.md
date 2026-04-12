# BUG: Root User Seed Only Runs on Empty DB

## Severity
Medium — recovery issue.

## Location
`crates/pomodoro-daemon/src/db/users.rs` — `seed_root_user`

## Description
`seed_root_user` checks `user_count == 0`. If all root users are deleted or demoted (leaving only normal users), there is no way to regain root access without direct DB manipulation.

## Scenario
1. Root demotes themselves (the only root) to `user` via `PUT /api/admin/users/{id}/role`.
2. No root users remain.
3. Daemon restarts — `seed_root_user` sees `count > 0`, skips seeding.
4. No one can access admin endpoints.

## Fix
Change seed condition to check for root users specifically:
```rust
let (root_count,): (i64,) = sqlx::query_as("SELECT COUNT(*) FROM users WHERE role = 'root'")
    .fetch_one(pool).await?;
if root_count == 0 {
    // seed root user
}
```
