# BUG: Logout Does Not Revoke Refresh Token

## Severity
Medium

## Location
`crates/pomodoro-daemon/src/routes/auth_routes.rs` — `logout`

## Description
The logout endpoint only revokes the access token from the `Authorization` header. The refresh token is not sent to the server and is not revoked.

## Impact
If an attacker captured the refresh token (e.g., from localStorage, XSS, or network sniffing on non-HTTPS), they can use it to obtain a new access token even after the user logs out.

## Fix
Option 1: Accept refresh token in logout body:
```rust
pub async fn logout(headers: HeaderMap, Json(body): Json<Option<LogoutRequest>>) -> ... {
    // Revoke access token
    auth::revoke_token(access_token).await;
    // Revoke refresh token if provided
    if let Some(req) = body {
        if let Some(rt) = req.refresh_token {
            auth::revoke_token(&rt).await;
        }
    }
}
```

Option 2: GUI sends refresh token in the logout request body.
