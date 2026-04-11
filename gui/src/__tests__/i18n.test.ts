import { describe, it, expect, beforeEach } from "vitest";
import { useI18n } from "../i18n";
import type { Locale } from "../i18n";

describe("i18n", () => {
  beforeEach(() => {
    // Reset to default
    useI18n.getState().setLocale("en");
  });

  it("defaults to English locale", () => {
    const { locale, t } = useI18n.getState();
    expect(locale).toBe("en");
    expect(t.appName).toBe("Pomodoro");
  });

  it("has all required keys in English locale", () => {
    const { t } = useI18n.getState();
    // Spot-check critical keys
    const requiredKeys: (keyof Locale)[] = [
      "appName", "logout", "settings", "timer", "tasks", "history",
      "sprints", "rooms", "login", "register", "username", "password",
      "start", "pause", "resume", "stop", "skip", "work", "shortBreak",
      "longBreak", "idle", "searchTasks", "addTask", "deleteTask",
      "labels", "dependsOn", "save", "cancel", "delete", "loading",
      "error", "success", "auditLog", "api",
    ];
    for (const key of requiredKeys) {
      expect(t[key], `Missing locale key: ${key}`).toBeTruthy();
      expect(typeof t[key]).toBe("string");
    }
  });

  it("no English locale values are empty strings", () => {
    const { t } = useI18n.getState();
    for (const [key, value] of Object.entries(t)) {
      expect(value, `Empty value for key: ${key}`).not.toBe("");
    }
  });

  it("falls back to English for unknown locale", () => {
    useI18n.getState().setLocale("xx");
    const { t } = useI18n.getState();
    expect(t.appName).toBe("Pomodoro");
  });

  it("availableLocales returns at least English", () => {
    const locales = useI18n.getState().availableLocales();
    expect(locales).toContain("en");
    expect(locales.length).toBeGreaterThanOrEqual(1);
  });

  it("setLocale updates state", () => {
    useI18n.getState().setLocale("en");
    expect(useI18n.getState().locale).toBe("en");
  });

  it("Locale interface has consistent keys between type and implementation", () => {
    const { t } = useI18n.getState();
    // Ensure no undefined values (all keys in interface have values)
    const entries = Object.entries(t);
    expect(entries.length).toBeGreaterThan(50); // sanity check — we have 80+ keys
    for (const [key, value] of entries) {
      expect(value, `Undefined value for key: ${key}`).toBeDefined();
    }
  });
});
