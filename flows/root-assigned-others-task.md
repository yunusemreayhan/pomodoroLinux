# Flow: Root User Is Assigned to a Task They Did Not Create

## Actor
Authenticated user with role `root`, assigned to another user's task.

## Steps

Same assignment mechanism as [user-assigned-others-task.md](user-assigned-others-task.md).

## Key Difference

Root bypasses all ownership checks via `is_owner_or_root()`, so the assignment is largely irrelevant for access control — root can already do everything.

| Operation | Normal Assignee | Root Assignee |
|---|---|---|
| Update task | ❌ | ✅ (root privilege, not assignee privilege) |
| Delete task | ❌ | ✅ |
| Remove own assignment | ❌ | ✅ (root can remove any assignee) |
| Remove other assignees | ❌ | ✅ |

## Notes
- The same bugs from the normal user flow apply (anyone can assign anyone, no auth check on `add_assignee`).
- Root doesn't need to be assigned to do anything — assignment is informational for root users.
