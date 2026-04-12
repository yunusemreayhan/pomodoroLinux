# BACKLOG v14 — Fresh Codebase Audit

Audit date: 2026-04-12
Status: **COMPLETE** — 30/30 items done

---

## Confirmed Bugs (8/8 ✅)

- [x] **B1.** Notification prefs disconnected from triggers — fixed: check prefs before creating
- [x] **B2.** FTS5 search leaks all users' tasks — fixed: user_id filter for non-root
- [x] **B3.** Time summary no ownership check — fixed: verify task exists
- [x] **B4.** Room list hardcoded SQL — fixed: use db::list_user_rooms with ROOM_SELECT
- [x] **B5.** Notification dropdown no outside click — fixed: mousedown listener
- [x] **B6.** Standup done uses updated_at — fixed: include today + require completed status
- [x] **B7.** WorkloadView sprints not loaded — fixed: added sprints to store + loadSprints
- [x] **B8.** Notifications unbounded — fixed: hourly cleanup of read >30 days

## Sprint & Scrum (8/8 ✅)

- [x] **BL1.** Ideal burndown line — already existed
- [x] **BL2.** Standup export — copy button with formatted markdown
- [x] **BL3.** Auto-unblock — blocked tasks move to backlog when all deps completed
- [x] **BL4.** Planning view — auto-selects backlog tab for planning sprints
- [x] **BL5.** Completion summary — toast with task/point/carryover stats
- [x] **BL6.** Cross-sprint tracking — sprint history shown on task detail
- [x] **BL7.** Scope change notifications — task owners notified on sprint add
- [x] **BL8.** WIP limit config — per-sprint input, persisted in localStorage

## Task Management (6/6 ✅)

- [x] **BL9.** Task activity feed — already existed (TaskActivityFeed component)
- [x] **BL10.** Template instantiation — fixed to use /instantiate endpoint
- [x] **BL11.** Bulk task operations — already existed (select/done/active/delete/sprint)
- [x] **BL12.** FTS5 search highlights — debounced search with <mark> snippets
- [x] **BL13.** Comment editing — inline edit with pencil icon, 15-min window
- [x] **BL14.** Password change — current password field + profile endpoint

## Estimation & Rooms (4/4 ✅)

- [x] **BL15.** Room task filtering — already works via TaskList search
- [x] **BL16.** Re-vote — already existed (🔄 Re-vote button)
- [x] **BL17.** Discussion timer — red warning + ⏰ when exceeding limit
- [x] **BL18.** Room share — copy room ID button for inviting

## Reporting & Analytics (4/4 ✅)

- [x] **BL19.** Project dashboard — completion rate bars per project
- [x] **BL20.** Weekly report CSV — export button on History page
- [x] **BL21.** Productivity trends — week-over-week focus/session comparison
- [x] **BL22.** Retro insights — velocity avg + trend direction on chart

---

## Commits (7)

1. `9c0cb17` — B1-B8: Fix all 8 confirmed bugs
2. `654e569` — BL2/BL6/BL10/BL13/BL14: Standup export, sprint history, templates, comments, password
3. `2ce572d` — BL5/BL8/BL21: Sprint completion summary, WIP config, productivity trends
4. `0fc270f` — BL3/BL7/BL20: Auto-unblock, scope notifications, weekly export
5. `34cf660` — BL12/BL19: FTS5 search highlights, project dashboard
6. `7493edb` — BL4/BL17/BL18/BL22: Planning view, discussion timer, room share, retro insights

## Test Results

- 275 backend tests passing
- 154 frontend tests passing
- TypeScript strict mode clean
