# BACKLOG v25 — Fresh Codebase Audit (2026-04-12)

Full audit of 58 backend .rs files (~6800 LOC), 66 frontend .ts/.tsx files (~9300 LOC), 275 backend tests, 154 frontend tests. Focused on previously unexamined areas: config, notify, main, lib, i18n, utils, tree, constants, App.tsx, ErrorBoundary, and cross-cutting edge cases.

## Bugs (2 items)

- [x] **B1.** `TASK_STATUSES` in `constants.ts` only has 4 statuses but backend has 8. The `TaskStatus` type was incomplete.
  **FIXED** (f78a308) — Added in_progress, blocked, done, estimated. Updated test.

- [x] **B2.** `Sidebar` theme toggle spreads `null` config when syncing to server, resetting all timer durations.
  **FIXED** (f78a308) — Guards against null config before PUT.

## Code Quality (1 item)

- [ ] **CQ1.** `build_router` uses `try_lock()` on tokio Mutex for CORS origins at startup.
  **WON'T FIX** — Only runs once at startup. Config lock is never held during router construction.

---

**Total: 3 items**
- **2 fixed:** B1, B2
- **1 won't fix:** CQ1
