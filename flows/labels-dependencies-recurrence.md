# Flow: Labels, Dependencies, Recurrence

## Labels
Global label pool, task-label assignment requires task ownership.

- `GET /api/labels` — list all labels. Any user.
- `POST /api/labels` — create label (name + color). Any user. No ownership.
- `DELETE /api/labels/{id}` — delete label. **Any user** (no ownership check).
- `PUT /api/tasks/{id}/labels/{label_id}` — assign label to task. **Owner or root.**
- `DELETE /api/tasks/{id}/labels/{label_id}` — remove label from task. **Owner or root.**
- `GET /api/tasks/{id}/labels` — list task's labels. Any user.

### ⚠️ BUG: Any User Can Delete Any Label
`delete_label` has no ownership check. Any user can delete globally shared labels.

## Dependencies
Task-to-task dependency links. Owner-gated.

- `GET /api/tasks/{id}/dependencies` — list dependencies. Any user.
- `POST /api/tasks/{id}/dependencies` — add dependency. **Owner or root.**
- `DELETE /api/tasks/{id}/dependencies/{dep_id}` — remove. **Owner or root.**
- `GET /api/dependencies` — list all dependencies globally. Any user.

## Recurrence
Recurring task patterns. Owner-gated.

- `PUT /api/tasks/{id}/recurrence` — set pattern (daily/weekly/biweekly/monthly) + next_due. **Owner or root.**
- `GET /api/tasks/{id}/recurrence` — get recurrence. Any user.
- `DELETE /api/tasks/{id}/recurrence` — remove. **Owner or root.**

### Background Processing (every 5 minutes)
1. Query recurrences where `next_due <= today` and `last_created != today`.
2. Clone the template task with title `"{original} ({date})"`.
3. Advance `next_due` based on pattern.
4. Broadcast `ChangeEvent::Tasks`.
