# BACKLOG v25 — Fresh Codebase Audit (2026-04-12)

Full audit of 58 backend .rs files (~6800 LOC), 66 frontend .ts/.tsx files (~9300 LOC), 275 backend tests, 154 frontend tests. Focused on previously unexamined areas: config, notify, main, lib, i18n, utils, tree, constants, App.tsx, ErrorBoundary, and cross-cutting edge cases.

## Bugs (2 items)

- [ ] **B1.** `TASK_STATUSES` in `constants.ts` is `["backlog", "active", "completed", "archived"]` but the backend `VALID_TASK_STATUSES` includes `"in_progress"`, `"blocked"`, `"done"`, and `"estimated"` as well. The frontend constant is incomplete — it's only used for type definitions, not validation, so no runtime impact. But the `TaskStatus` type is wrong.

- [ ] **B2.** `Sidebar` in `App.tsx` calls `apiCall("PUT", "/api/config", { ...cur, theme: th })` to sync theme to server. But `cur` is `useStore.getState().config` which may be `null` if config hasn't loaded yet. Spreading `null` produces an empty object, so the PUT would send `{ theme: "dark" }` with all other config fields missing, which would reset all timer durations to their defaults on the server.

## Code Quality (1 item)

- [ ] **CQ1.** `build_router` in `lib.rs` uses `engine.config.try_lock()` (non-async `Mutex::try_lock`) to read CORS origins. If the lock is held (e.g., during config update), `try_lock` returns `None` and CORS origins from config are silently skipped. This only affects startup and is unlikely to cause issues, but `try_lock` on a tokio Mutex is a code smell.

---

**Total: 3 items**

Priority order: B2 (theme sync resets config), B1 (type mismatch), CQ1 (try_lock).
