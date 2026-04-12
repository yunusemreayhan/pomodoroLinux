# BUG: No Audit Log on Role Change

## Severity
Low — compliance/traceability.

## Location
`crates/pomodoro-daemon/src/routes/admin.rs` — `update_user_role`

## Description
The `update_user_role` handler changes a user's role but does not create an audit log entry. Role changes are security-sensitive operations that should be tracked.

## Fix
```rust
db::update_user_role(&engine.pool, id, &req.role).await.map_err(internal)?;
db::audit(&engine.pool, claims.user_id, "update_role", "user", Some(id), Some(&req.role)).await.ok();
```
