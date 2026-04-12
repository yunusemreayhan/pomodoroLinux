# BUG: Any User Can Delete Any Label

## Severity
Low

## Location
`crates/pomodoro-daemon/src/routes/labels.rs` — `delete_label`

## Description
The `delete_label` endpoint has no ownership or role check. `_claims` is unused. Any authenticated user can delete any globally shared label, affecting all tasks that use it.

## Fix
Either restrict to root, or track label creator and check ownership:
```rust
if claims.role != "root" {
    return Err(err(StatusCode::FORBIDDEN, "Root only"));
}
```
