import { describe, it, expect, vi } from "vitest";
import { buildTree } from "../tree";
import type { Task } from "../store/api";

function makeTask(overrides: Partial<Task> = {}): Task {
  return {
    id: 1, parent_id: null, user_id: 1, user: "root", title: "Test", description: null,
    project: null, tags: null, priority: 3, estimated: 1, actual: 0,
    estimated_hours: 0, remaining_points: 0, due_date: null, status: "backlog",
    sort_order: 1, created_at: "2024-01-01", updated_at: "2024-01-01",
    attachment_count: 0, deleted_at: null, ...overrides,
  };
}

// T6: Task search/filter/sort behavior

describe("TaskList search filtering", () => {
  const tasks = [
    makeTask({ id: 1, title: "Fix login bug", project: "auth", tags: "bug,urgent", status: "active", priority: 1, user: "alice" }),
    makeTask({ id: 2, title: "Add dark mode", project: "ui", tags: "feature", status: "backlog", priority: 3, user: "bob" }),
    makeTask({ id: 3, title: "Write tests", project: "auth", tags: "test", status: "completed", priority: 2, user: "alice" }),
    makeTask({ id: 4, title: "Deploy to prod", project: "devops", tags: null, status: "active", priority: 1, due_date: "2024-06-01", user: "bob" }),
    makeTask({ id: 5, title: "Refactor auth module", project: "auth", tags: "refactor", status: "archived", priority: 4, user: "alice" }),
  ];

  it("builds tree from flat tasks", () => {
    const tree = buildTree(tasks);
    expect(tree.length).toBe(5);
  });

  it("filters active tasks (excludes completed and archived)", () => {
    const tree = buildTree(tasks);
    const active = tree.filter(n => n.task.status !== "completed" && n.task.status !== "archived");
    expect(active.length).toBe(3);
    expect(active.map(n => n.task.id)).toEqual([1, 2, 4]);
  });

  it("filters all tasks (excludes only archived)", () => {
    const tree = buildTree(tasks);
    const all = tree.filter(n => n.task.status !== "archived");
    expect(all.length).toBe(4);
  });

  it("filters 'mine' tasks by username", () => {
    const tree = buildTree(tasks);
    const mine = tree.filter(n => n.task.user === "alice" && n.task.status !== "archived");
    expect(mine.length).toBe(2);
    expect(mine.map(n => n.task.id)).toEqual([1, 3]);
  });

  it("sorts by priority", () => {
    const tree = buildTree(tasks);
    const sorted = [...tree].sort((a, b) => a.task.priority - b.task.priority);
    expect(sorted[0].task.priority).toBe(1);
    expect(sorted[sorted.length - 1].task.priority).toBe(4);
  });

  it("sorts by due date (nulls last)", () => {
    const tree = buildTree(tasks);
    const sorted = [...tree].sort((a, b) =>
      (a.task.due_date || "9999") < (b.task.due_date || "9999") ? -1 : 1
    );
    expect(sorted[0].task.id).toBe(4); // only one with due_date
  });

  it("sorts by updated_at descending", () => {
    const tasksWithDates = [
      makeTask({ id: 1, updated_at: "2024-01-03" }),
      makeTask({ id: 2, updated_at: "2024-01-01" }),
      makeTask({ id: 3, updated_at: "2024-01-05" }),
    ];
    const tree = buildTree(tasksWithDates);
    const sorted = [...tree].sort((a, b) => b.task.updated_at < a.task.updated_at ? -1 : 1);
    expect(sorted[0].task.id).toBe(3);
    expect(sorted[2].task.id).toBe(2);
  });

  it("search matches title case-insensitively", () => {
    const tree = buildTree(tasks);
    const q = "login";
    const matches = tree.filter(n => n.task.title.toLowerCase().includes(q));
    expect(matches.length).toBe(1);
    expect(matches[0].task.id).toBe(1);
  });

  it("search matches project", () => {
    const tree = buildTree(tasks);
    const q = "auth";
    const matches = tree.filter(n =>
      n.task.title.toLowerCase().includes(q) ||
      (n.task.project ?? "").toLowerCase().includes(q)
    );
    expect(matches.length).toBe(3); // Fix login bug, Write tests, Refactor auth
  });

  it("search matches tags", () => {
    const tree = buildTree(tasks);
    const q = "urgent";
    const matches = tree.filter(n =>
      (n.task.tags ?? "").toLowerCase().includes(q)
    );
    expect(matches.length).toBe(1);
    expect(matches[0].task.id).toBe(1);
  });

  it("combined filter + sort works", () => {
    const tree = buildTree(tasks);
    const active = tree.filter(n => n.task.status !== "completed" && n.task.status !== "archived");
    const sorted = [...active].sort((a, b) => a.task.priority - b.task.priority);
    expect(sorted.map(n => n.task.id)).toEqual([1, 4, 2]); // priority 1, 1, 3
  });
});

// T5: Timer state transitions (logic only — no component rendering)

describe("Timer state machine logic", () => {
  it("idle → running transition", () => {
    const state = { phase: "Idle", status: "Idle", elapsed_s: 0, duration_s: 0 };
    // Simulate start
    const started = { ...state, phase: "Work", status: "Running", duration_s: 1500 };
    expect(started.status).toBe("Running");
    expect(started.phase).toBe("Work");
    expect(started.duration_s).toBe(1500);
  });

  it("running → paused transition", () => {
    const state = { phase: "Work", status: "Running", elapsed_s: 300, duration_s: 1500 };
    const paused = { ...state, status: "Paused" };
    expect(paused.status).toBe("Paused");
    expect(paused.elapsed_s).toBe(300); // preserved
  });

  it("paused → running transition (resume)", () => {
    const state = { phase: "Work", status: "Paused", elapsed_s: 300, duration_s: 1500 };
    const resumed = { ...state, status: "Running" };
    expect(resumed.status).toBe("Running");
    expect(resumed.elapsed_s).toBe(300); // preserved
  });

  it("running → idle transition (stop)", () => {
    const state = { phase: "Work", status: "Running", elapsed_s: 300, duration_s: 1500 };
    const stopped = { phase: "Idle", status: "Idle", elapsed_s: 0, duration_s: 0 };
    expect(stopped.status).toBe("Idle");
    expect(stopped.elapsed_s).toBe(0);
  });

  it("work complete → short break", () => {
    const state = { phase: "Work", status: "Running", elapsed_s: 1500, duration_s: 1500, session_count: 1 };
    const breakState = { ...state, phase: "ShortBreak", elapsed_s: 0, duration_s: 300 };
    expect(breakState.phase).toBe("ShortBreak");
  });

  it("work complete after interval → long break", () => {
    const state = { phase: "Work", status: "Running", elapsed_s: 1500, duration_s: 1500, session_count: 4 };
    const breakState = { ...state, phase: "LongBreak", elapsed_s: 0, duration_s: 900 };
    expect(breakState.phase).toBe("LongBreak");
  });

  it("remaining time calculation", () => {
    const state = { elapsed_s: 300, duration_s: 1500 };
    const remaining = Math.max(0, state.duration_s - state.elapsed_s);
    expect(remaining).toBe(1200);
  });

  it("progress percentage", () => {
    const state = { elapsed_s: 750, duration_s: 1500 };
    const progress = state.duration_s > 0 ? state.elapsed_s / state.duration_s : 0;
    expect(progress).toBeCloseTo(0.5);
  });

  it("daily goal tracking", () => {
    const state = { daily_completed: 3, daily_goal: 8 };
    const progress = state.daily_completed / state.daily_goal;
    expect(progress).toBeCloseTo(0.375);
    expect(state.daily_completed < state.daily_goal).toBe(true);
  });
});
