# BUG: Token Refresh Uses Wrong Server's Refresh Token

## Severity
Medium — breaks multi-server usage.

## Location
`gui/src/store/api.ts` — `tryRefreshToken`

## Description
`tryRefreshToken()` always reads `state.savedServers?.[0]?.refresh_token`. The `savedServers` array is ordered by most-recently-logged-in. If the user switches to a different server (not the most recent), the refresh function sends the wrong server's refresh token to the current server.

## Scenario
1. User logs into Server A (savedServers[0] = A).
2. User switches to Server B (savedServers[0] = B, savedServers[1] = A).
3. User switches back to Server A via `switchToServer`.
4. `serverUrl` is now A, but `savedServers[0]` is still B.
5. Access token for A expires → `tryRefreshToken()` sends B's refresh token to A → fails.
6. User gets logged out.

## Fix
Find the matching server entry by current `serverUrl` and `username`:
```typescript
const state = useStore.getState();
const server = state.savedServers.find(
  s => s.url === state.serverUrl && s.username === state.username
);
if (!server?.refresh_token) return false;
```
