# Flow: Root Resets User Password (Admin)

## Actor
Authenticated user with role `root`.

## Steps

1. Root sends `PUT /api/admin/users/{id}/password` with `{"password": "NewPass123"}`.
2. Checks `claims.role == "root"` → `403` if not.
3. `validate_password` → must be 8+ chars, uppercase, digit.
4. Hash with bcrypt cost 12.
5. `db::update_user_password` → updates hash in DB.
6. Audit log entry: `action: "admin_reset_password"`.
7. Returns `204 No Content`.

## What Happens to the Target User
- Their **existing tokens remain valid** — password change does not invalidate tokens.
- The user can continue using the app with their old tokens until they expire.
- On next login, they must use the new password.

## ⚠️ BUG: Password Reset Does Not Invalidate Tokens

After an admin resets a user's password (e.g., because the account was compromised), the old tokens continue to work. The attacker's stolen tokens remain valid for up to 2 hours (access) or 30 days (refresh).

See `backlog/password-reset-no-token-invalidation.md`.
