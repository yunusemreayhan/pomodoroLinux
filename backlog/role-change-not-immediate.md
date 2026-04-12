# BUG: Role Change Not Reflected Until Token Expires

## Severity
Medium — security concern for demotions.

## Location
`crates/pomodoro-daemon/src/auth.rs` — JWT claims contain `role` at issuance time.

## Description
When a root user changes another user's role via `PUT /api/admin/users/{id}/role`, the change is written to the DB but the user's existing access token still contains the old role. The old role is used for all authorization checks until:
- The access token expires (up to 2 hours), or
- The user refreshes their token (which re-fetches from DB).

## Impact
- **Promotion** (user → root): User doesn't get root powers until token refresh. Low impact.
- **Demotion** (root → user): User retains root powers for up to 2 hours. **Security risk.**

## Fix
On role change, invalidate all of the target user's tokens. Options:
1. Add a `token_version` column to users table, increment on role change, check in `Claims` extractor.
2. Revoke all tokens for the user (requires tracking issued tokens per user).
3. Reduce access token expiry to a shorter window (e.g., 15 minutes).
