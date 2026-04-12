# BUG: No Option to Disable Public Registration

## Severity
Medium — security concern in shared networks.

## Location
`crates/pomodoro-daemon/src/routes/auth_routes.rs` — `register`

## Description
The `POST /api/auth/register` endpoint is always open. Anyone who can reach the daemon can create accounts. There is no config option, env var, or admin setting to disable registration.

## Impact
In a team environment where the daemon is exposed on a LAN, unauthorized users can create accounts and access all tasks (since all tasks are visible to all authenticated users).

## Fix
Add a config option `allow_registration` (default: `true`):
```rust
if !engine.get_config().await.allow_registration {
    return Err(err(StatusCode::FORBIDDEN, "Registration is disabled"));
}
```
Or an env var `POMODORO_ALLOW_REGISTRATION=false`.
