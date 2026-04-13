# Backlog V48 — Full Codebase Audit (2026-04-13)

Scope: Stability, correctness, security, performance, UX, accessibility, code quality.
No new features.

---

## V48-1 [Medium / Security] `update_webhook` doesn't validate URL for SSRF (private IPs)
**File:** `routes/webhooks.rs:update_webhook`
`create_webhook` validates the URL against private/loopback addresses, but `update_webhook` only checks the scheme prefix. A user could create a webhook with a valid URL, then update it to point to `http://127.0.0.1/...`.

## V48-2 [Medium / Bug] `get_sprint_root_tasks` doesn't check sprint existence — returns empty instead of 404
**File:** `routes/epics.rs:84-86`
Returns `[]` for non-existent sprint IDs.

---

## Summary

| ID | Severity | Category | Status |
|----|----------|----------|--------|
| V48-1 | Medium | Security | FIXED — validates SSRF like create_webhook |
| V48-2 | Medium | Bug | FIXED — returns 404 for non-existent sprint |

**Total: 2 items** — 2 fixed
