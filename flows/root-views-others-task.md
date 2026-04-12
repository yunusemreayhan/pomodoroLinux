# Flow: Root User Views a Task They Did Not Create

## Actor
Authenticated user with role `root`, viewing another user's task.

## Steps

Identical to [user-views-others-task.md](user-views-others-task.md). All tasks are visible to all users.

## Root Privileges on Other Users' Tasks

Unlike normal users, root can also **mutate** tasks they don't own:

| Operation | Normal User (non-owner) | Root (non-owner) |
|---|---|---|
| View task | ✅ | ✅ |
| Update task | ❌ `403 Not owner` | ✅ `is_owner_or_root()` |
| Delete task | ❌ `403 Not owner` | ✅ `is_owner_or_root()` |
| Restore deleted task | ❌ `403 Not owner` | ✅ `is_owner_or_root()` |
| Reorder tasks | ❌ `403` (ownership batch check) | ✅ (skips check) |
| Bulk status update | ❌ `403` (ownership batch check) | ✅ (skips check) |
| Remove assignee | ❌ `403 Not owner` | ✅ `is_owner_or_root()` |
| Update session note | ❌ `403 Not session owner` | ✅ `is_owner_or_root()` |
| Comment | ✅ | ✅ |
| Start timer | ✅ | ✅ |
