# BUG: Root Can Demote Self to Last Non-Root User

## Severity
High — can lock out all admin access.

## Location
`crates/pomodoro-daemon/src/routes/admin.rs` — `update_user_role`

## Description
A root user can change their own role to `user` via `PUT /api/admin/users/{self_id}/role {"role": "user"}`. There is no check for whether this would leave zero root users.

The "last root user" protection only exists in `delete_user`, not in `update_user_role`.

## Scenario
1. Only one root user exists (id=1).
2. Root sends `PUT /api/admin/users/1/role {"role": "user"}`.
3. Succeeds — now zero root users in the system.
4. No one can access any `/api/admin/*` endpoint.
5. `seed_root_user` won't help because `user_count > 0`.

## Fix
```rust
if req.role != "root" && user.role == "root" {
    let (root_count,): (i64,) = sqlx::query_as("SELECT COUNT(*) FROM users WHERE role = 'root'")
        .fetch_one(&engine.pool).await.map_err(internal)?;
    if root_count <= 1 {
        return Err(err(StatusCode::BAD_REQUEST, "Cannot demote the last root user"));
    }
}
```
