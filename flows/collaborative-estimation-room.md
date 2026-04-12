# Flow: Collaborative Estimation Session (Planning Poker Room)

## Actor
Multiple authenticated users collaborating in a real-time estimation room.

## Room Lifecycle

```
lobby → voting → revealed → lobby (next task) → ... → closed
```

## Steps

### 1. Create Room
- Any user sends `POST /api/rooms` with `{"name": "Sprint Planning", "estimation_unit": "points"}`.
- Creator becomes room admin automatically.
- Limit: 20 active rooms per user.
- Valid estimation units: `points`, `hours`, `mandays`, `tshirt`.

### 2. Join Room
- Other users send `POST /api/rooms/{id}/join`.
- **No invitation required** — any authenticated user can join any room.
- New members get role `voter` by default.

### 3. Start Voting on a Task
- Room admin sends `POST /api/rooms/{id}/start-voting` with `{"task_id": 42}`.
- Room status changes to `voting`.
- Task must exist and not be soft-deleted.

### 4. Cast Votes
- Each member sends `POST /api/rooms/{id}/vote` with `{"value": 5}`.
- Must be a room member (non-root users checked).
- Observers cannot vote.
- Vote value: 0–1000.
- Room must be in `voting` state.

### 5. Reveal Votes
- Room admin sends `POST /api/rooms/{id}/reveal`.
- Room status changes to `revealed`.
- All votes become visible to members.

### 6. Accept Estimate
- Room admin sends `POST /api/rooms/{id}/accept` with `{"value": 5}`.
- Writes the accepted value to the task's estimation field (`estimated` for points, `estimated_hours` for hours).
- Task status set to `estimated`.
- **Auto-advances** to next unestimated leaf task in the room, or returns to `lobby` if all done.

### 7. Close Room
- Room admin sends `POST /api/rooms/{id}/close`.
- Room status set to `closed`.

## Real-Time Updates
- WebSocket at `/api/rooms/{id}/ws?ticket=...` pushes room state changes.
- Uses SSE ticket auth (same as timer SSE).
- Only sends updates when state actually changes (dedup check).

## Room Roles

| Role | Can vote | Can admin (start/reveal/accept/kick) |
|---|---|---|
| `admin` | ✅ | ✅ |
| `voter` | ✅ | ❌ |
| `observer` | ❌ | ❌ |

- Room creator is auto-admin.
- Admins can change other members' roles via `PUT /api/rooms/{id}/role`.
- Admins can kick members via `DELETE /api/rooms/{id}/members/{username}`.

## Authorization Summary

| Action | Room Admin | Room Voter | Non-member | Root (non-member) |
|---|---|---|---|---|
| View room state | ✅ | ✅ | ✅ | ✅ |
| Join room | ✅ | ✅ | ✅ | ✅ |
| Cast vote | ✅ | ✅ | ❌ | ✅ |
| Start voting | ✅ | ❌ | ❌ | ✅ |
| Reveal votes | ✅ | ❌ | ❌ | ✅ |
| Accept estimate | ✅ | ❌ | ❌ | ✅ |
| Kick member | ✅ | ❌ | ❌ | ✅ |
| Close room | ✅ | ❌ | ❌ | ✅ |
| Delete room | Owner only | ❌ | ❌ | ✅ |
| Export history | ✅ | ✅ | ❌ | ✅ |

## ⚠️ BUG: Room State Visible to Non-Members

`get_room_state` (`GET /api/rooms/{id}`) has no membership check — `_claims` is unused. Any authenticated user can see the full room state including votes. The `list_rooms` endpoint correctly filters for non-root users, but direct access by ID is open. See `backlog/room-state-no-membership-check.md`.

## ⚠️ BUG: Accept Estimate Writes to Any Task

When `accept_estimate` writes the voted value to the task, it does not check if the room admin owns the task. This means a room admin can overwrite the estimation of any task in the system, even tasks owned by other users. This is arguably by design for collaborative estimation, but it bypasses the normal `is_owner_or_root` check. See `backlog/accept-estimate-bypasses-ownership.md`.
