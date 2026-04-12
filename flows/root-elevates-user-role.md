# Flow: Root Elevates User Role

## Actor
Authenticated user with role `root`.

## Steps

1. Root sends `PUT /api/admin/users/{id}/role` with `{"role": "root"}`.
2. Checks `claims.role == "root"` → `403` if not.
3. Validates role is one of: `["user", "root"]`.
4. `db::update_user_role` → `UPDATE users SET role = ? WHERE id = ?`.
5. Returns updated user object.

## What Happens to the Elevated User
- Their **existing tokens still contain the old role** (`"user"`) in JWT claims.
- The role change takes effect:
  - **Immediately** on next login (fresh token).
  - **On next token refresh** — `refresh_token` endpoint re-fetches user from DB.
  - **NOT** on current access token — it still says `role: "user"` until it expires (up to 2h).

## Demoting a User (root → user)
Same endpoint: `PUT /api/admin/users/{id}/role` with `{"role": "user"}`.

Same delayed-effect problem: the demoted user retains root privileges until their access token expires or they refresh.

## ⚠️ BUG: No Audit Log on Role Change

The `update_user_role` handler does not create an audit log entry. Role changes are security-sensitive and should be audited.

See `backlog/role-change-no-audit.md`.

## ⚠️ BUG: Can Demote Self

A root user can demote themselves to `user`. If they're the last root user, this doesn't fail — the check for "last root user" only exists in `delete_user`, not in `update_user_role`. This could lock everyone out of admin functions.

See `backlog/root-can-demote-self-to-last.md`.
