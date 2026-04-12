# BUG: Password Reset Does Not Invalidate Existing Tokens

## Severity
Medium — security concern.

## Location
`crates/pomodoro-daemon/src/routes/admin.rs` — `admin_reset_password`
`crates/pomodoro-daemon/src/routes/auth_routes.rs` — `change_password`
`crates/pomodoro-daemon/src/routes/profile.rs` — `update_profile`

## Description
When a password is changed (by admin reset or self-service), existing access and refresh tokens remain valid. JWT tokens are stateless — the password is not part of the token claims, so changing it has no effect on token validity.

## Impact
If an admin resets a user's password because the account was compromised, the attacker's stolen tokens continue to work for up to 2 hours (access) or 30 days (refresh).

## Fix
On password change, invalidate all tokens for the user. Options:
1. Add a `token_version` or `password_changed_at` field to users, embed in JWT claims, check on validation.
2. Track all issued tokens per user and revoke them on password change.
3. At minimum, invalidate the user cache so the next DB check happens immediately.
