# Flow: User Changes Own Password

## Actor
Authenticated user (any role).

## Two Endpoints

### 1. Via Auth Route: `PUT /api/auth/password`
1. User sends `{"current_password": "OldPass1", "new_password": "NewPass1"}`.
2. `validate_password` on new password.
3. Fetches user from DB, verifies current password with bcrypt.
4. Wrong current password → `401 "Current password is incorrect"`.
5. Hash new password, update DB.
6. Returns `204 No Content`.
7. **Does NOT return new tokens** — user keeps using existing token.

### 2. Via Profile Route: `PUT /api/profile`
1. User sends `{"password": "NewPass1", "current_password": "OldPass1"}`.
2. `current_password` is **required** when changing password (V3 validation).
3. Missing → `400 "current_password is required to change password"`.
4. Wrong → `403 "Current password is incorrect"`.
5. Hash new password, update DB.
6. **Returns new tokens** (access + refresh) — unlike the auth route.
7. Can also change username in the same request.

## Difference Between the Two
| | `PUT /api/auth/password` | `PUT /api/profile` |
|---|---|---|
| Returns new tokens | ❌ | ✅ |
| Can change username | ❌ | ✅ |
| Error code for wrong password | `401` | `403` |

## ⚠️ Note: Inconsistent Error Codes
The auth route returns `401 Unauthorized` for wrong current password, while the profile route returns `403 Forbidden`. Both should use the same code.
