# Flow: Task Templates

## Purpose
Save task configurations as reusable templates with variable resolution.

## CRUD
- `GET /api/templates` — list templates owned by current user.
- `POST /api/templates` — create. Per-user, max 100. Data is JSON blob (max 64KB).
- `DELETE /api/templates/{id}` — owner or root.

## Instantiate (`POST /api/templates/{id}/instantiate`)
1. Owner or root only.
2. Parses template JSON data.
3. Resolves variables in title and description:
   - `{{today}}` → current date (YYYY-MM-DD)
   - `{{username}}` → current user's username
4. Creates a new task with resolved values.
5. Returns the created task.

## Template Data Format
```json
{
  "title": "Daily standup {{today}}",
  "description": "Notes for {{username}}",
  "project": "TeamSync",
  "priority": 2,
  "estimated": 1
}
```

## Authorization
Templates are per-user. Users can only see/use their own templates. Root can access all.
