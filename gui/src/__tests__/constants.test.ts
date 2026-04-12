import { describe, it, expect } from "vitest";
import { PRIORITY_COLORS, TASK_STATUSES, SPRINT_STATUSES } from "../constants";

describe("PRIORITY_COLORS", () => {
  it("has 6 entries (index 0 unused, 1-5 for priorities)", () => {
    expect(PRIORITY_COLORS.length).toBe(6);
  });

  it("index 0 is empty (unused)", () => {
    expect(PRIORITY_COLORS[0]).toBe("");
  });

  it("indices 1-5 are valid hex colors", () => {
    for (let i = 1; i <= 5; i++) {
      expect(PRIORITY_COLORS[i]).toMatch(/^#[0-9A-Fa-f]{6}$/);
    }
  });
});

describe("TASK_STATUSES", () => {
  it("contains expected statuses", () => {
    expect(TASK_STATUSES).toContain("backlog");
    expect(TASK_STATUSES).toContain("active");
    expect(TASK_STATUSES).toContain("completed");
    expect(TASK_STATUSES).toContain("archived");
  });

  it("has exactly 8 statuses", () => {
    expect(TASK_STATUSES.length).toBe(8);
  });
});

describe("SPRINT_STATUSES", () => {
  it("contains expected statuses", () => {
    expect(SPRINT_STATUSES).toContain("planning");
    expect(SPRINT_STATUSES).toContain("active");
    expect(SPRINT_STATUSES).toContain("completed");
  });

  it("has exactly 3 statuses", () => {
    expect(SPRINT_STATUSES.length).toBe(3);
  });
});
