# Flow: SSE Ticket Authentication

## Purpose
SSE (Server-Sent Events) uses `EventSource` which cannot set custom headers. JWT tokens in query strings leak into logs. Solution: short-lived opaque tickets.

## Steps

1. GUI sends `POST /api/timer/ticket` with Bearer access token.
2. Backend validates access token (normal `Claims` extractor).
3. Generates 24-byte random ticket (hex-encoded, 48 chars) from `/dev/urandom`.
4. Stores `ticket → (user_id, created_at)` in in-memory HashMap.
5. **Per-user limit**: max 5 active tickets per user → `429 Too Many Requests`.
6. **Cleanup**: when map > 50 entries, prune tickets older than 30 seconds.
7. Returns `{"ticket": "..."}`.

## SSE Connection
1. GUI opens `EventSource` to `/api/timer/sse?ticket=<ticket>`.
2. Backend looks up ticket in HashMap:
   - Not found → `401 "Invalid or expired ticket"`.
   - Found but > 30 seconds old → `401 "Ticket expired"`.
   - Valid → removes ticket (one-time use), extracts `user_id`.
3. SSE stream starts, sends initial timer state for that user.
4. Subsequent events pushed via broadcast channels.

## Room WebSocket
Same ticket mechanism for `/api/rooms/{id}/ws?ticket=<ticket>`.
Additional check: user must be a room member.

## Security Properties
- Tickets are one-time use (removed on consumption).
- 30-second expiry window.
- Max 5 concurrent tickets per user.
- No JWT in URL/logs.
- Ticket does not contain any claims — just maps to a user_id server-side.
