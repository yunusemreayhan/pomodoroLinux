import { describe, it, expect } from "vitest";
import { matchSearch } from "../utils";

describe("matchSearch", () => {
  it("returns true for empty query", () => {
    expect(matchSearch("anything", "")).toBe(true);
  });

  it("matches case-insensitively", () => {
    expect(matchSearch("Hello World", "hello")).toBe(true);
    expect(matchSearch("Hello World", "WORLD")).toBe(true);
  });

  it("matches with regex patterns", () => {
    expect(matchSearch("backend-api-v2", "api.*v2")).toBe(true);
    expect(matchSearch("task-123", "\\d+")).toBe(true);
    expect(matchSearch("foo bar", "^foo")).toBe(true);
  });

  it("returns false for no match", () => {
    expect(matchSearch("Hello", "xyz")).toBe(false);
    expect(matchSearch("", "something")).toBe(false);
  });

  it("falls back to string match on invalid regex", () => {
    expect(matchSearch("test [bracket", "[bracket")).toBe(true);
    expect(matchSearch("test (paren", "(paren")).toBe(true);
    expect(matchSearch("test +plus", "+plus")).toBe(true);
  });

  it("handles special characters in text", () => {
    expect(matchSearch("C++ programming", "c\\+\\+")).toBe(true);
    expect(matchSearch("file.txt", "file\\.txt")).toBe(true);
  });

  it("matches partial strings", () => {
    expect(matchSearch("authentication", "auth")).toBe(true);
    expect(matchSearch("authentication", "tion")).toBe(true);
  });
});
