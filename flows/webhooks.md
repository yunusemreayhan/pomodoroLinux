# Flow: Webhooks

## Purpose
HTTP callbacks on task/sprint events.

## CRUD
- `GET /api/webhooks` — list webhooks owned by current user.
- `POST /api/webhooks` — create. URL validation:
  - Must start with `http://` or `https://`.
  - No embedded credentials.
  - Blocked: localhost, 127.0.0.1, private ranges (10.x, 192.168.x, 172.16-31.x), link-local, .local domains.
  - Events: `*` (all) or comma-separated: `task.created`, `task.updated`, `task.deleted`, `sprint.created`, `sprint.started`, `sprint.completed`.
  - Optional `secret` for HMAC signing.
- `DELETE /api/webhooks/{id}` — owner only (checked by `delete_webhook` in DB layer).

## Dispatch
`webhook::dispatch()` called from task/sprint route handlers:
- Spawns async task.
- Filters webhooks by event type.
- POST to webhook URL with JSON payload.
- If secret set: HMAC-SHA256 signature in `X-Webhook-Signature` header.

## Authorization
Per-user. Users only see/manage their own webhooks.
