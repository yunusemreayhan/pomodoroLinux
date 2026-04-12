# BACKLOG v14 — Fresh Codebase Audit

Audit date: 2026-04-12
Codebase: 6266 LOC backend (55 .rs files), 8992 LOC frontend (53 .ts/.tsx files)
Tests: 239 backend, 154 frontend

Focus: Only confirmed bugs + business logic improvements (per user guidance)

---

## Confirmed Bugs (8)

**B1.** Notification triggers (BL21-23 from v13) never check `notification_prefs` before creating notifications. A user who disabled `task_assigned` events still gets assignment notifications. The prefs table and UI exist but are completely disconnected from the notification creation code in `assignees.rs`, `sprints.rs`, and `comments.rs`.

**B2.** `search_tasks` endpoint (`GET /api/tasks/search`) has no user filtering — any authenticated user can search all users' tasks including titles and description snippets. The regular `list_tasks` properly filters by user, but the FTS5 search bypasses this entirely.

**B3.** `get_task_time_summary` has no ownership check — any authenticated user can see detailed per-user time tracking for any task by ID. Should verify task ownership or at minimum check the task exists.

**B4.** `list_rooms` for non-root users builds SQL by string concatenation with a hardcoded SELECT. If the `Room` struct fields change, this query silently breaks. Should use the same `ROOM_SELECT` constant pattern used elsewhere.

**B5.** `NotificationBell` component in `App.tsx` polls `/api/notifications/unread` every 30s but the dropdown doesn't close when clicking outside. Clicking anywhere else on the page while the dropdown is open leaves it floating.

**B6.** `StandupView` in Dashboard checks `t.status === "completed" && t.updated_at.startsWith(yesterday)` for "done yesterday" — but `updated_at` changes on ANY update, not just status changes. A task completed last week that gets a comment edit today would show as "done yesterday".

**B7.** `WorkloadView` in Dashboard uses `taskSprintsMap` which maps task_id → sprint info, but the sprint info doesn't include sprint status. It filters by `activeSprintIds` from the `sprints` array, but `sprints` in the store is only loaded on the Sprints page — it's empty on Dashboard initial load.

**B8.** Notifications table has no retention/cleanup. Unlike audit_log (which has no cleanup either but is admin-only), notifications grow per-user unboundedly. After months of use, `list_notifications` will scan thousands of rows per user.

---

## Business Logic — Sprint & Scrum (8)

**BL1.** Sprint burndown chart should show ideal burn line — a straight line from total points at sprint start to 0 at sprint end. Currently the burndown only shows actual progress, making it hard to see if the team is ahead or behind schedule.

**BL2.** Sprint daily standup export — add a "Copy standup" button that generates a formatted standup message (per-user done/wip/blocked) for pasting into Slack/Teams. The data is already computed in `StandupView`.

**BL3.** Sprint task auto-status — when all dependencies of a blocked task are completed, automatically move it from "blocked" to "backlog" (or "in_progress" if it was previously in progress). Currently blocked tasks stay blocked forever until manually moved.

**BL4.** Sprint planning view — when in "planning" status, show a dedicated planning interface: drag tasks from backlog into sprint, see capacity vs load in real-time, highlight unestimated tasks prominently. Currently planning and active sprints use the same UI.

**BL5.** Sprint completion summary — when completing a sprint, show a modal with: velocity, goal met status, carried-over tasks count, and prompt for retro notes. Currently it just silently changes status.

**BL6.** Cross-sprint task tracking — when a task appears in multiple sprints (via carryover), show the sprint history on the task detail view. Currently there's no way to see which sprints a task has been part of.

**BL7.** Sprint scope change notification — when tasks are added/removed from an active sprint, notify affected team members (task owners/assignees). Currently only audit log captures this (BL8 from v13).

**BL8.** Sprint board WIP limit configuration — the WIP limit is hardcoded to 5 in `SprintParts.tsx`. Should be configurable per sprint (stored in sprint metadata or config).

---

## Business Logic — Task Management (6)

**BL9.** Task activity feed — on the task detail view, show a unified timeline of: status changes, comments, time logs, assignment changes, sprint additions. Currently these are shown in separate sections with no chronological context.

**BL10.** Task templates UI — the `POST /api/templates/{id}/instantiate` endpoint exists but the frontend `TemplateManager` only has create/delete. Add a "Use template" button that creates a task from the template.

**BL11.** Bulk task operations UI — the `PUT /api/tasks/bulk-status` endpoint exists but there's no frontend UI for selecting multiple tasks and changing their status. Add checkbox selection mode to TaskList.

**BL12.** Task search results page — the `GET /api/tasks/search` endpoint returns highlighted snippets with `<mark>` tags but the frontend search in `TaskList.tsx` uses the regular `list_tasks` endpoint with `?search=` parameter. Should use the FTS5 search endpoint and render highlights.

**BL13.** Comment editing UI — the `PUT /api/comments/{id}` endpoint exists (with 15-min window) but `CommentSection.tsx` has no edit button or inline editing. Users can only delete and re-add comments.

**BL14.** Password change UI — the `PUT /api/auth/password` endpoint exists but there's no frontend form in Settings to change password. Users must use the API directly.

---

## Business Logic — Estimation & Rooms (4)

**BL15.** Room task filtering — in estimation rooms, the task list shows ALL tasks. Should allow filtering by project, status, or sprint to focus on relevant tasks during planning poker.

**BL16.** Re-vote capability — after revealing votes, if the team wants to discuss and re-vote on the same task, there's no "Re-vote" button. The admin must manually start voting on the same task again.

**BL17.** Estimation room timer — add a configurable discussion timer (e.g., 2 minutes) that starts after votes are revealed. Helps keep estimation meetings focused. The elapsed timer already exists but only tracks total time, not per-discussion.

**BL18.** Room invitation link — currently users must know the room ID to join. Add a shareable invite link or code that non-members can use to join a room.

---

## Business Logic — Reporting & Analytics (4)

**BL19.** Project-level dashboard — show aggregated stats per project: total tasks, completion rate, total hours logged, active sprint progress. Currently there's no project-level view.

**BL20.** Time tracking weekly report — generate a weekly summary of hours logged per task/project, exportable as CSV. The data exists in burn_log but isn't aggregated by week.

**BL21.** Personal productivity trends — on the History page, show week-over-week comparison: "This week vs last week" for focus hours, sessions completed, tasks done. The raw data exists but isn't compared.

**BL22.** Sprint retrospective insights — after multiple sprints, show trends: velocity trend, estimation accuracy trend, scope change frequency. Help teams improve their process over time.

---

## Summary

| Category                        | Count |
|---------------------------------|-------|
| Confirmed Bugs                  | 8     |
| Sprint & Scrum                  | 8     |
| Task Management                 | 6     |
| Estimation & Rooms              | 4     |
| Reporting & Analytics           | 4     |
| **Total**                       | **30** |
