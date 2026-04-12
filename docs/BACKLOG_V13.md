# BACKLOG v13 — Confirmed Bugs + Business Logic

Audit date: 2026-04-12
Status: **COMPLETE** — 30/30 items done

---

## Confirmed Bugs (7/7 ✅)

- [x] **B1.** Mutex held during DB queries in `get_active_timers` — fixed: snapshot under lock, query after
- [x] **B2.** UTF-8 panic in `export.rs` title slice — fixed: `chars().take(50)`
- [x] **B3.** `unwrap()` panic in `admin.rs` serialization — fixed: `map_err(internal)?`
- [x] **B4.** Comment edit window never enforced — fixed: reject on parse failure
- [x] **B5.** User hours report drops end day — fixed: append `T23:59:59`
- [x] **B6.** Duplicate `aria-label` in Dependencies.tsx — fixed: removed duplicate
- [x] **B7.** N+1 API calls for sprint board labels — fixed: use store's `taskLabelsMap`

## Sprint & Scrum Workflow (10/10 ✅)

- [x] **BL1.** Sprint progress widget on Dashboard (board status, % bar, WIP items)
- [x] **BL2.** "My tasks" badge on sprint list items
- [x] **BL3.** Daily standup view (yesterday done, today WIP, blocked per user)
- [x] **BL4.** Sprint goal tracking ("Goal met?" checkbox)
- [x] **BL5.** "Blocked" task status + 4-column sprint board
- [x] **BL6.** Sprint velocity — already existed (VelocityChart + /api/sprints/velocity)
- [x] **BL7.** Blocked task detection (unresolved deps shown on board cards)
- [x] **BL8.** Sprint scope change audit (task add/remove logged)
- [x] **BL9.** Team workload view (hours/points per user in active sprints)
- [x] **BL10.** Sprint retro workflow — already existed (structured template)

## Timer & Productivity (5/5 ✅)

- [x] **BL11.** Focus time report (weekly/monthly/avg daily/active days/best day)
- [x] **BL12.** Estimation accuracy in sprint summary (estimate vs actual variance)
- [x] **BL13.** Break compliance tracking (break-to-work ratio with color coding)
- [x] **BL14.** Session notes prompt after work session completes
- [x] **BL15.** Daily goal celebration toast

## Estimation & Planning (5/5 ✅)

- [x] **BL16.** Estimation accuracy report (room estimate vs actual in vote history)
- [x] **BL17.** Planning poker history (similar task estimates shown during voting)
- [x] **BL18.** Sprint capacity planning (hours vs capacity with over-capacity warning)
- [x] **BL19.** Unestimated task warning in sprint backlog
- [x] **BL20.** Estimation confidence (high variance warning in vote history)

## Notifications & Awareness (3/3 ✅)

- [x] **BL21.** Task assignment notifications
- [x] **BL22.** Sprint start/complete notifications to team
- [x] **BL23.** Comment @mention notifications

---

## Commits (7)

1. `2e7a20a` — B1-B7: Fix all 7 confirmed bugs
2. `a70b077` — BL1/BL3/BL5: Sprint progress, standup view, blocked status
3. `837c5f2` — BL7/BL8/BL12/BL14/BL15: Board blockers, audit, estimation, notes
4. `8a5bdc2` — BL4/BL9/BL18/BL19/BL20: Goal tracking, workload, capacity, estimation
5. `9d0f4fb` — BL2/BL11/BL13: Sprint visibility, focus report, break compliance
6. `dc3702d` — BL21/BL22/BL23: In-app notification system
7. `69439da` — BL16/BL17: Estimation accuracy report + planning poker history

## Test Results

- 239 backend tests passing
- 154 frontend tests passing
- TypeScript strict mode clean
