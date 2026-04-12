# Flow: Epic Groups

## Purpose
Epics group tasks for high-level tracking with burndown snapshots.

## CRUD
- `POST /api/epics` — any user. Creator is owner. Max 100 globally.
- `GET /api/epics` — list all. No auth filter.
- `GET /api/epics/{id}` — detail with tasks and snapshots.
- `DELETE /api/epics/{id}` — owner or root.

## Task Management
- `POST /api/epics/{id}/tasks` — owner or root. Adds task IDs. Validates tasks exist and not deleted.
- `DELETE /api/epics/{id}/tasks/{task_id}` — owner or root.

## Snapshots
- `POST /api/epics/{id}/snapshot` — owner or root. Manual snapshot.
- Automatic hourly snapshots for all epic groups (background task in main.rs).

## Authorization
Owner-based (`created_by`) + root override. Same pattern as sprints.
