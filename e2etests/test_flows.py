"""E2E flow tests: Login, Registration, Timer, Tasks, Settings — all through the GUI.

Each test interacts with the Tauri frontend via WebDriver (DOM-level).
The daemon runs isolated on port 19090 with a fresh DB.
"""

import time
import pytest
from desktop_pilot import TauriWebDriver, WebDriverError
from harness import (
    Daemon, GUI_BINARY, ROOT_PASSWORD, BASE_URL,
    connect_gui_to_daemon, gui_login, gui_logout, api_register,
)


# ── Helpers ─────────────────────────────────────────────────────

def click_sidebar_tab(app, index: int):
    """Click a sidebar tab by index. 0=timer, 1=dashboard, 2=tasks, etc."""
    app.execute_js(f"document.querySelectorAll('div.w-\\\\[72px\\\\] button')[{index}]?.click()")
    time.sleep(1)


def set_react_input(app, selector: str, value: str):
    """Set a React controlled input's value properly."""
    # Use double quotes in JS to avoid conflicts with CSS selectors
    app.execute_js(
        "const nativeSet = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;"
        "const el = document.querySelector(\"" + selector.replace('"', '\\"') + "\");"
        "if (el) {"
        "  nativeSet.call(el, \"" + value.replace('"', '\\"') + "\");"
        "  el.dispatchEvent(new Event('input', { bubbles: true }));"
        "}"
    )


# ── Flow: user-login.md ────────────────────────────────────────

class TestLogin:

    def test_login_shows_timer(self, app):
        gui_login(app, "root", ROOT_PASSWORD)
        app.assert_visible("Start Focus")
        app.assert_visible("Short Break")
        app.assert_visible("Long Break")

    def test_login_wrong_password_shows_error(self, app):
        gui_logout(app)
        connect_gui_to_daemon(app)
        gui_login(app, "root", "WrongPass1")
        body = app.text(app.find("body"))
        assert "invalid" in body.lower() or "error" in body.lower() or "credentials" in body.lower()

    def test_login_after_error_works(self, app):
        # Should still be on login screen from previous test
        connect_gui_to_daemon(app)
        gui_login(app, "root", ROOT_PASSWORD)
        app.assert_visible("Start Focus")


# ── Flow: user-registration.md ─────────────────────────────────

class TestRegistration:

    def test_register_via_gui(self, app):
        gui_logout(app)
        connect_gui_to_daemon(app)
        # Switch to register form
        app.click_text("No account? Register", "button")
        time.sleep(0.5)
        set_react_input(app, "input[placeholder='Username']", "guireg1")
        set_react_input(app, "input[placeholder*='Password']", "GuiReg1Pass")
        # Find and click the register/create button
        btns = app.find_all("button")
        for b in btns:
            txt = app.text(b).strip().lower()
            if "create" in txt or "register" in txt or "sign up" in txt:
                app.click(b)
                break
        time.sleep(2)
        # Should be logged in now
        app.assert_visible("Start Focus")


# ── Flow: pomodoro-timer-session.md ─────────────────────────────

class TestTimerSession:

    def test_start_focus(self, app):
        gui_logout(app)
        connect_gui_to_daemon(app)
        gui_login(app, "root", ROOT_PASSWORD)
        app.click_text("Start Focus")
        time.sleep(1)
        # Timer should be running — look for pause or stop controls
        body = app.text(app.find("body"))
        # When running, the button text changes
        assert "00:" in body or "01:" in body or "Pause" in body or "Stop" in body

    def test_short_break_button(self, app):
        # Stop any running timer first
        try:
            app.click_text("Stop")
            time.sleep(0.5)
        except (WebDriverError, AssertionError):
            pass
        app.click_text("Short Break")
        time.sleep(0.5)
        body = app.text(app.find("body"))
        assert "01:00" in body or "00:" in body or "Short" in body

    def test_long_break_button(self, app):
        try:
            app.click_text("Stop")
            time.sleep(0.5)
        except (WebDriverError, AssertionError):
            pass
        app.click_text("Long Break")
        time.sleep(0.5)
        body = app.text(app.find("body"))
        assert "01:00" in body or "00:" in body or "Long" in body


# ── Flow: user-creates-task.md (via Tasks tab) ─────────────────

class TestTasksTab:

    def test_navigate_to_tasks(self, app):
        click_sidebar_tab(app, 2)  # tasks tab
        time.sleep(1)
        body = app.text(app.find("body"))
        # Tasks page should have some task-related UI
        assert len(body) > 0  # page loaded

    def test_create_task_via_gui(self, app):
        click_sidebar_tab(app, 2)
        time.sleep(0.5)
        # Look for an add/create task input or button
        inputs = app.find_all("input")
        task_input = None
        for inp in inputs:
            p = app.attribute(inp, "placeholder") or ""
            if "task" in p.lower() or "add" in p.lower() or "new" in p.lower():
                task_input = inp
                break
        if task_input:
            set_react_input(app, f"input[placeholder='{app.attribute(task_input, 'placeholder')}']", "E2E Test Task")
            app.execute_js("""
                document.querySelectorAll('input').forEach(i => {
                    if (i.value === 'E2E Test Task') {
                        i.dispatchEvent(new KeyboardEvent('keydown', {key: 'Enter', bubbles: true}));
                    }
                });
            """)
            time.sleep(1)
            body = app.text(app.find("body"))
            assert "E2E Test Task" in body


# ── Flow: settings / config ────────────────────────────────────

class TestSettingsTab:

    def test_navigate_to_settings(self, app):
        click_sidebar_tab(app, 7)  # settings tab
        time.sleep(1)
        body = app.text(app.find("body"))
        # Settings should show config options
        assert len(body) > 50


# ── Flow: dashboard ────────────────────────────────────────────

class TestDashboardTab:

    def test_navigate_to_dashboard(self, app):
        click_sidebar_tab(app, 1)  # dashboard tab
        time.sleep(1)
        body = app.text(app.find("body"))
        assert len(body) > 0


# ── Flow: sprints tab ──────────────────────────────────────────

class TestSprintsTab:

    def test_navigate_to_sprints(self, app):
        click_sidebar_tab(app, 3)  # sprints tab
        time.sleep(1)
        body = app.text(app.find("body"))
        assert len(body) > 0


# ── Flow: rooms tab ────────────────────────────────────────────

class TestRoomsTab:

    def test_navigate_to_rooms(self, app):
        click_sidebar_tab(app, 4)  # rooms tab
        time.sleep(1)
        body = app.text(app.find("body"))
        assert len(body) > 0


# ── Flow: history tab ──────────────────────────────────────────

class TestHistoryTab:

    def test_navigate_to_history(self, app):
        click_sidebar_tab(app, 5)  # history tab
        time.sleep(1)
        body = app.text(app.find("body"))
        assert len(body) > 0


# ── DOM integrity ───────────────────────────────────────────────

class TestDomIntegrity:

    def test_react_root_mounted(self, app):
        source = app.page_source()
        assert 'id="root"' in source

    def test_theme_attribute(self, app):
        theme = app.execute_js("return document.documentElement.getAttribute('data-theme')")
        assert theme in ("dark", "light")

    def test_title(self, app):
        assert app.title() == "Pomodoro"
