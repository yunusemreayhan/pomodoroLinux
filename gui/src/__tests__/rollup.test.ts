import { describe, it, expect } from "vitest";
import { computeRollup } from "../rollup";
import type { Task, TaskDetail, Session } from "../store/api";

function task(overrides: Partial<Task> = {}): Task {
  return {
    id: 1, parent_id: null, user_id: 1, user: "root", title: "T", description: null,
    project: null, tags: null, priority: 3, estimated: 1, actual: 0,
    estimated_hours: 0, remaining_points: 0, due_date: null, status: "backlog",
    sort_order: 0, created_at: "", updated_at: "", attachment_count: 0, deleted_at: null, work_duration_minutes: null, estimate_optimistic: null, estimate_pessimistic: null, ...overrides,
  };
}

function session(duration_s: number): Session {
  return { id: 1, task_id: 1, user_id: 1, user: "root", session_type: "work", status: "completed", started_at: "", ended_at: null, duration_s, notes: null };
}

function detail(overrides: Partial<TaskDetail> = {}): TaskDetail {
  return { task: task(), comments: [], sessions: [], children: [], ...overrides };
}

describe("computeRollup", () => {
  it("empty task returns zeros", () => {
    const r = computeRollup(detail({ task: task({ estimated: 0 }) }), new Map());
    expect(r.ownEstHours).toBe(0);
    expect(r.ownSpentHours).toBe(0);
    expect(r.ownEstPoints).toBe(0);
    expect(r.ownRemPoints).toBe(0);
    expect(r.ownSessionSecs).toBe(0);
    expect(r.totalEstHours).toBe(0);
    expect(r.totalSpentHours).toBe(0);
    expect(r.progressHours).toBeNull();
    expect(r.progressPoints).toBeNull();
  });

  it("own hours from hoursMap", () => {
    const r = computeRollup(detail({ task: task({ id: 5, estimated_hours: 10 }) }), new Map([[5, 3]]));
    expect(r.ownSpentHours).toBe(3);
    expect(r.progressHours).toBe(30);
  });

  it("session seconds summed", () => {
    const r = computeRollup(detail({ sessions: [session(1500), session(1200)] }), new Map());
    expect(r.ownSessionSecs).toBe(2700);
    expect(r.totalSessionSecs).toBe(2700);
  });

  it("points progress", () => {
    const r = computeRollup(detail({ task: task({ estimated: 10, remaining_points: 3 }) }), new Map());
    expect(r.progressPoints).toBe(70);
  });

  it("progress capped at 100", () => {
    const r = computeRollup(detail({ task: task({ id: 1, estimated_hours: 5 }) }), new Map([[1, 20]]));
    expect(r.progressHours).toBe(100);
  });

  it("zero estimates → null progress", () => {
    const r = computeRollup(detail({ task: task({ estimated_hours: 0, estimated: 0 }) }), new Map());
    expect(r.progressHours).toBeNull();
    expect(r.progressPoints).toBeNull();
  });

  it("child rollup", () => {
    const child = detail({
      task: task({ id: 2, estimated_hours: 5, estimated: 3, remaining_points: 1 }),
      sessions: [session(600)],
    });
    const parent = detail({
      task: task({ id: 1, estimated_hours: 10, estimated: 5, remaining_points: 2 }),
      children: [child],
    });
    const r = computeRollup(parent, new Map([[1, 3], [2, 2]]));
    expect(r.totalEstHours).toBe(15);
    expect(r.totalSpentHours).toBe(5);
    expect(r.childEstHours).toBe(5);
    expect(r.childSpentHours).toBe(2);
    expect(r.totalEstPoints).toBe(8);
    expect(r.totalRemPoints).toBe(3);
    expect(r.totalSessionSecs).toBe(600);
  });

  it("deep nesting (3 levels)", () => {
    const gc = detail({ task: task({ id: 3, estimated_hours: 1, estimated: 1, remaining_points: 0 }) });
    const ch = detail({ task: task({ id: 2, estimated_hours: 2, estimated: 2, remaining_points: 1 }), children: [gc] });
    const root = detail({ task: task({ id: 1, estimated_hours: 3, estimated: 3, remaining_points: 0 }), children: [ch] });
    const r = computeRollup(root, new Map([[1, 1], [2, 1], [3, 0.5]]));
    expect(r.totalEstHours).toBe(6);
    expect(r.totalSpentHours).toBe(2.5);
    expect(r.totalEstPoints).toBe(6);
    expect(r.totalRemPoints).toBe(1);
    expect(r.progressPoints).toBe(83); // (6-1)/6 = 83%
  });

  it("multiple children at same level", () => {
    const c1 = detail({ task: task({ id: 2, estimated_hours: 5 }) });
    const c2 = detail({ task: task({ id: 3, estimated_hours: 3 }) });
    const root = detail({ task: task({ id: 1, estimated_hours: 2 }), children: [c1, c2] });
    const r = computeRollup(root, new Map());
    expect(r.totalEstHours).toBe(10);
    expect(r.childEstHours).toBe(8);
  });

  it("missing task in hoursMap returns 0 spent", () => {
    const r = computeRollup(detail({ task: task({ id: 99, estimated_hours: 10 }) }), new Map());
    expect(r.ownSpentHours).toBe(0);
    expect(r.progressHours).toBe(0);
  });
});
