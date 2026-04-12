# BUG: Room State Visible to Non-Members

## Severity
Low

## Location
`crates/pomodoro-daemon/src/routes/rooms.rs` — `get_room_state`

## Description
The `GET /api/rooms/{id}` endpoint (`get_room_state`) does not check room membership. The `_claims` parameter is unused. Any authenticated user can view the full room state, including:
- All members and their roles
- Current voting task
- All cast votes (after reveal)
- Vote history

Meanwhile, `list_rooms` correctly filters non-root users to only see rooms they're members of. This creates an inconsistency — you can't discover rooms you're not in via the list, but you can access them directly by ID.

## Current Behavior
```
User A creates Room 1, Users B and C join.
User D (not a member) sends GET /api/rooms/1.
→ 200 OK — full room state returned.
```

## Expected Behavior
Non-members should get `403 Forbidden` when accessing room state directly, unless they are root.

## Fix
```rust
pub async fn get_room_state(State(engine): State<AppState>, claims: Claims, Path(id): Path<i64>) -> ApiResult<db::RoomState> {
    let state = db::get_room_state(&engine.pool, id).await.map_err(internal)?;
    if claims.role != "root" && !state.members.iter().any(|m| m.user_id == claims.user_id) {
        return Err(err(StatusCode::FORBIDDEN, "Not a room member"));
    }
    Ok(Json(state))
}
```

## Impact
Low — room data is not sensitive in most team contexts, but violates the access model set by `list_rooms`.
