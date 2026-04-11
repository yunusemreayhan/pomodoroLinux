import { describe, it, expect } from "vitest";
import { buildTree, countDescendants } from "../tree";
import type { Task } from "../store/api";

function t(id: number, parent_id: number | null = null, sort_order = 0): Task {
  return {
    id, parent_id, user_id: 1, user: "root", title: `Task ${id}`, description: null,
    project: null, tags: null, priority: 3, estimated: 1, actual: 0,
    estimated_hours: 0, remaining_points: 0, due_date: null, status: "backlog",
    sort_order, created_at: "", updated_at: "", attachment_count: 0,
  };
}

describe("buildTree", () => {
  it("empty input returns empty array", () => {
    expect(buildTree([])).toEqual([]);
  });

  it("single task becomes root", () => {
    const tree = buildTree([t(1)]);
    expect(tree.length).toBe(1);
    expect(tree[0].task.id).toBe(1);
    expect(tree[0].children).toEqual([]);
  });

  it("flat list — all roots", () => {
    const tree = buildTree([t(1), t(2), t(3)]);
    expect(tree.length).toBe(3);
  });

  it("parent-child nesting", () => {
    const tree = buildTree([t(1), t(2, 1), t(3, 1)]);
    expect(tree.length).toBe(1);
    expect(tree[0].children.length).toBe(2);
    expect(tree[0].children[0].task.id).toBe(2);
    expect(tree[0].children[1].task.id).toBe(3);
  });

  it("three-level nesting", () => {
    const tree = buildTree([t(1), t(2, 1), t(3, 2)]);
    expect(tree.length).toBe(1);
    expect(tree[0].children[0].children[0].task.id).toBe(3);
  });

  it("orphaned children (missing parent) become roots", () => {
    const tree = buildTree([t(5, 999)]);
    expect(tree.length).toBe(1);
    expect(tree[0].task.id).toBe(5);
  });

  it("mixed roots and children", () => {
    const tree = buildTree([t(1), t(2), t(3, 1), t(4, 2), t(5, 1)]);
    expect(tree.length).toBe(2);
    const r1 = tree.find(n => n.task.id === 1)!;
    const r2 = tree.find(n => n.task.id === 2)!;
    expect(r1.children.length).toBe(2);
    expect(r2.children.length).toBe(1);
  });

  it("preserves task data", () => {
    const task = { ...t(1), title: "Custom Title", priority: 5, status: "active" as const };
    const tree = buildTree([task]);
    expect(tree[0].task.title).toBe("Custom Title");
    expect(tree[0].task.priority).toBe(5);
    expect(tree[0].task.status).toBe("active");
  });

  it("handles 100 tasks efficiently", () => {
    const tasks = Array.from({ length: 100 }, (_, i) => t(i + 1, i === 0 ? null : 1));
    const tree = buildTree(tasks);
    expect(tree.length).toBe(1);
    expect(tree[0].children.length).toBe(99);
  });
});

describe("countDescendants", () => {
  it("leaf node returns 0", () => {
    const tree = buildTree([t(1)]);
    expect(countDescendants(tree[0])).toBe(0);
  });

  it("one child returns 1", () => {
    const tree = buildTree([t(1), t(2, 1)]);
    expect(countDescendants(tree[0])).toBe(1);
  });

  it("nested children counted recursively", () => {
    const tree = buildTree([t(1), t(2, 1), t(3, 2), t(4, 3)]);
    expect(countDescendants(tree[0])).toBe(3);
  });

  it("wide tree", () => {
    const tasks = [t(1), ...Array.from({ length: 10 }, (_, i) => t(i + 2, 1))];
    const tree = buildTree(tasks);
    expect(countDescendants(tree[0])).toBe(10);
  });

  it("mixed depth", () => {
    // 1 -> 2 -> 4
    //   -> 3
    const tree = buildTree([t(1), t(2, 1), t(3, 1), t(4, 2)]);
    expect(countDescendants(tree[0])).toBe(3);
    const child2 = tree[0].children.find(c => c.task.id === 2)!;
    expect(countDescendants(child2)).toBe(1);
    const child3 = tree[0].children.find(c => c.task.id === 3)!;
    expect(countDescendants(child3)).toBe(0);
  });
});
