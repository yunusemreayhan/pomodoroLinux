export const PRIORITY_COLORS = ["", "#10B981", "#4ECDC4", "#F59E0B", "#FF6B6B", "#EF4444"];

export const TASK_STATUSES = ["backlog", "active", "in_progress", "blocked", "completed", "done", "estimated", "archived"] as const;
export type TaskStatus = typeof TASK_STATUSES[number];

export const SPRINT_STATUSES = ["planning", "active", "completed"] as const;
export type SprintStatus = typeof SPRINT_STATUSES[number];
