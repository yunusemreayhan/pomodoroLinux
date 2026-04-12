# Flow: Teams

## Purpose
Teams group users and scope task visibility via "root tasks" (top-level task trees).

## Create Team
- `POST /api/teams` — any user. Creator auto-added as `admin`.
- Max 50 teams globally.

## Members
- `POST /api/teams/{id}/members` — team admin or root. Roles: `admin`, `member`.
- `DELETE /api/teams/{id}/members/{user_id}` — team admin or root.
- `GET /api/me/teams` — list teams the current user belongs to.

## Root Tasks (Scope)
- `POST /api/teams/{id}/roots` — team admin or root. Adds task IDs as team root tasks.
- `DELETE /api/teams/{id}/roots/{task_id}` — team admin or root.
- `GET /api/teams/{id}/scope` — returns all task IDs in the team's scope (root tasks + descendants).

## Delete Team
- `DELETE /api/teams/{id}` — **root only** (not team admin).

## Authorization
| Action | Team Admin | Team Member | Non-member | Root |
|---|---|---|---|---|
| View team | ✅ | ✅ | ✅ | ✅ |
| Add/remove members | ✅ | ❌ | ❌ | ✅ |
| Add/remove root tasks | ✅ | ❌ | ❌ | ✅ |
| Delete team | ❌ | ❌ | ❌ | ✅ |

## GUI Usage
- User selects active team → `setActiveTeam(teamId)`.
- Store fetches team scope → filters task list to only show scoped tasks.
- `activeTeamId` persisted in localStorage.
