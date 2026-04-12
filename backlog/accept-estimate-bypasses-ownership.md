# DESIGN: Accept Estimate Bypasses Task Ownership

## Severity
Low — likely by design, but worth documenting.

## Location
`crates/pomodoro-daemon/src/routes/rooms.rs` — `accept_estimate`

## Description
When a room admin accepts an estimation vote, the accepted value is written directly to the task's `estimated` or `estimated_hours` field via `db::accept_estimate`. This does **not** check `is_owner_or_root` on the task.

This means a room admin can overwrite the estimation of any task in the system, as long as voting was started on that task in their room.

## Current Behavior
```
User A creates Task 1.
User B creates Room 1, starts voting on Task 1, team votes, B accepts estimate of 8.
→ Task 1's estimated field is set to 8, even though User B doesn't own Task 1.
```

## Analysis
This is probably **correct behavior** for collaborative estimation — the whole point of planning poker is that the team decides the estimate, not the task owner. However:

1. It's an implicit exception to the ownership model.
2. Any room admin can target any task, not just tasks in their project/sprint.
3. The task status is also changed to `estimated` without owner consent.

## Recommendation
If this is by design, document it. If not, add a check that the task belongs to the room's project scope, or that the task owner is a room member.
