# BUG: Default Root Password Bypasses Validation Rules

## Severity
Low — security hygiene.

## Location
`crates/pomodoro-daemon/src/db/users.rs` — `seed_root_user`

## Description
The seeded root password is `"root"` (4 chars, no uppercase, no digit). The `validate_password` function requires 8+ chars, uppercase, and digit. The seed bypasses this because it calls `db::create_user` directly.

This means:
- The root user exists with a password that violates the system's own rules.
- There is no forced password change on first login.
- The weak default password works indefinitely.

## Fix
Either:
1. Use a stronger default password that meets validation rules, or
2. Generate a random password on first boot and print it to logs, or
3. Add a "must change password" flag that forces password change on first login.
