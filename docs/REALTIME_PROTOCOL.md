# Real-time Protocol

## Server-Sent Events (SSE)

The primary real-time channel. Connect to `GET /api/events` with a Bearer token.

### Connection
```
GET /api/events
Authorization: Bearer <token>
Accept: text/event-stream
```

### Event Types

| Event | Data | Trigger |
|---|---|---|
| `timer` | `EngineState` JSON | Every tick (1s) while any timer is running |
| `tasks` | `"changed"` | Task created, updated, deleted, or restored |
| `sprints` | `"changed"` | Sprint created, started, completed, or modified |
| `rooms` | `"changed"` | Room state change (vote, reveal, accept) |
| `config` | `"changed"` | User or global config updated |

### Client Handling
- On `tasks`/`sprints`/`rooms`/`config` events: refetch the relevant data
- On `timer` events: update the timer display directly from the payload
- Reconnect with exponential backoff (1s, 2s, 4s, ..., max 30s)

## WebSocket (Estimation Rooms)

Used for real-time room interaction. Connect to `GET /api/rooms/{id}/ws`.

### Connection
```
ws://localhost:3030/api/rooms/{id}/ws?token=<jwt>
```

### Messages (Server → Client)
JSON messages with `type` field:
- `state` — Full room state update
- `vote` — A member cast a vote
- `reveal` — Votes revealed
- `accept` — Estimate accepted

### Messages (Client → Server)
Not used — all actions go through REST endpoints. The WebSocket is receive-only for real-time updates.
