# Flow: Watchers & Notifications

## Task Watchers
- `POST /api/tasks/{id}/watch` — watch a task. Self-only (uses `claims.user_id`).
- `DELETE /api/tasks/{id}/watch` — unwatch.
- `GET /api/tasks/{id}/watchers` — list watcher usernames. Any user.
- `GET /api/watched` — list task IDs the current user is watching.

No ownership check — any user can watch any task.

## Notification Preferences
Per-user, per-event-type toggles:
- `GET /api/profile/notifications` — returns preferences for all event types.
- `PUT /api/profile/notifications` — update preferences.

Event types: `task_assigned`, `task_completed`, `comment_added`, `sprint_started`, `sprint_completed`, `time_logged`.

Default: all enabled.

## Desktop Notifications
Triggered by the tick loop when a timer session completes:
1. Check user's `notify_desktop` config (default: enabled).
2. If enabled: send desktop notification via `notify::notify_session_complete`.
3. Optional sound (`notify_sound` config).

## Due Date Reminders (every 30 minutes)
Background task checks for tasks due today or tomorrow:
- Sends desktop notification: `"{title}" is {overdue|due tomorrow}`.
- Tracks notified task IDs per day to avoid duplicates.
