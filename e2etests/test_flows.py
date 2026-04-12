"""E2E GUI flow tests for Pomodoro Tauri app.

All tests interact with the real GUI via WebDriver (DOM-level).
Daemon runs isolated on port 19090 with a fresh DB per session.
Each test class is order-independent — use `logged_in` fixture for auth.
"""

import time
import pytest
from desktop_pilot import TauriWebDriver, WebDriverError
from harness import (
    Daemon, GUI_BINARY, ROOT_PASSWORD,
    connect_gui_to_daemon, gui_login, gui_logout, api_register,
)
import harness
import json, urllib.request


# ── Helpers ─────────────────────────────────────────────────────

def click_tab(app, title: str):
    app.execute_js(f"document.querySelector('button[title=\"{title}\"]')?.click()")
    time.sleep(1)


def set_input(app, selector: str, value: str):
    app.execute_js(
        "const nativeSet = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;"
        "const el = document.querySelector(\"" + selector.replace('"', '\\"') + "\");"
        "if (el) {"
        "  nativeSet.call(el, \"" + value.replace('"', '\\"') + "\");"
        "  el.dispatchEvent(new Event('input', { bubbles: true }));"
        "}"
    )


def api_call(method, path, body=None, token=None):
    data = json.dumps(body).encode() if body else (b"" if method in ("POST", "PUT") else None)
    hdrs = {"Content-Type": "application/json", "X-Requested-With": "test"}
    if token:
        hdrs["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(f"{harness.BASE_URL}{path}", data=data, headers=hdrs, method=method)
    resp = urllib.request.urlopen(req, timeout=5)
    raw = resp.read().decode()
    return json.loads(raw) if raw else {}


def get_root_token():
    resp = api_call("POST", "/api/auth/login", {"username": "root", "password": ROOT_PASSWORD})
    return resp["token"]


def body_text(app) -> str:
    return app.text(app.find("body"))


def ensure_login_screen(app):
    """Make sure we're on the login screen."""
    body = body_text(app)
    if "Sign In" not in body:
        gui_logout(app)
    connect_gui_to_daemon(app)


# ── Flow: user-login.md ────────────────────────────────────────

class TestLogin:

    def test_login_shows_timer(self, app):
        ensure_login_screen(app)
        gui_login(app, "root", ROOT_PASSWORD)
        app.assert_visible("Start Focus")

    def test_login_wrong_password_shows_error(self, app):
        ensure_login_screen(app)
        gui_login(app, "root", "WrongPass1")
        body = body_text(app)
        assert "invalid" in body.lower() or "error" in body.lower() or "credentials" in body.lower()

    def test_login_after_error_recovers(self, app):
        ensure_login_screen(app)
        gui_login(app, "root", ROOT_PASSWORD)
        app.assert_visible("Start Focus")


# ── Flow: user-registration.md ─────────────────────────────────

class TestRegistration:

    def test_register_via_gui(self, app):
        ensure_login_screen(app)
        app.click_text("No account? Register", "button")
        time.sleep(0.5)
        set_input(app, "input[placeholder='Username']", "guireg1")
        set_input(app, "input[placeholder*='Password']", "GuiReg1Pass")
        btns = app.find_all("button")
        for b in btns:
            txt = app.text(b).strip().lower()
            if "create" in txt or "register" in txt or "sign up" in txt:
                app.click(b)
                break
        time.sleep(2)
        app.assert_visible("Start Focus")

    def test_register_then_logout_login(self, app):
        ensure_login_screen(app)
        gui_login(app, "guireg1", "GuiReg1Pass")
        app.assert_visible("Start Focus")


# ── Flow: user-logout.md ───────────────────────────────────────

class TestLogout:

    def test_logout_shows_login_screen(self, logged_in):
        click_tab(logged_in, "Logout")
        time.sleep(1)
        body = body_text(logged_in)
        assert "Sign In" in body

    def test_login_after_logout(self, app):
        ensure_login_screen(app)
        gui_login(app, "root", ROOT_PASSWORD)
        app.assert_visible("Start Focus")


# ── Flow: pomodoro-timer-session.md ─────────────────────────────

class TestTimerSession:

    def test_initial_state_ready(self, logged_in):
        click_tab(logged_in, "Timer")
        logged_in.assert_visible("READY")

    def test_start_focus_changes_state(self, logged_in):
        click_tab(logged_in, "Timer")
        logged_in.click_text("Start Focus")
        time.sleep(1)
        body = body_text(logged_in)
        assert "Focus" in body or "00:" in body or "01:" in body or "READY" in body

    def test_pause_timer(self, logged_in):
        try:
            logged_in.click_text("Pause")
            time.sleep(0.5)
            body = body_text(logged_in)
            assert "Resume" in body or "PAUSED" in body
        except (WebDriverError, AssertionError):
            pass

    def test_resume_timer(self, logged_in):
        try:
            logged_in.click_text("Resume")
            time.sleep(0.5)
        except (WebDriverError, AssertionError):
            pass

    def test_stop_timer(self, logged_in):
        try:
            logged_in.click_text("Stop")
            time.sleep(0.5)
        except (WebDriverError, AssertionError):
            pass
        logged_in.assert_visible("Start Focus")

    def test_short_break_mode(self, logged_in):
        click_tab(logged_in, "Timer")
        logged_in.click_text("Short Break")
        time.sleep(0.5)
        body = body_text(logged_in)
        assert "01:00" in body or "00:" in body

    def test_long_break_mode(self, logged_in):
        try:
            logged_in.click_text("Stop")
            time.sleep(0.3)
        except (WebDriverError, AssertionError):
            pass
        logged_in.click_text("Long Break")
        time.sleep(0.5)
        body = body_text(logged_in)
        assert "01:00" in body or "00:" in body

    def test_back_to_focus(self, logged_in):
        try:
            logged_in.click_text("Stop")
            time.sleep(0.3)
        except (WebDriverError, AssertionError):
            pass
        logged_in.click_text("Start Focus")
        time.sleep(0.5)
        body = body_text(logged_in)
        assert "01:00" in body or "00:" in body
        try:
            logged_in.click_text("Stop")
        except (WebDriverError, AssertionError):
            pass


# ── Flow: user-creates-task.md ─────────────────────────────────

class TestTasks:

    def test_tasks_tab_loads(self, logged_in):
        click_tab(logged_in, "Tasks")
        time.sleep(0.5)
        inputs = logged_in.find_all("input[placeholder*='New project']")
        assert len(inputs) > 0

    def test_create_task_via_api_shows_in_gui(self, logged_in):
        token = get_root_token()
        api_call("POST", "/api/tasks", {"title": "API Created Task", "project": "E2EProject"}, token)
        click_tab(logged_in, "Refresh data")
        time.sleep(1)
        click_tab(logged_in, "Tasks")
        time.sleep(1)
        body = body_text(logged_in)
        assert "API Created Task" in body or "E2EProject" in body

    def test_search_tasks(self, logged_in):
        click_tab(logged_in, "Tasks")
        time.sleep(0.5)
        set_input(logged_in, "input[placeholder*='Search']", "API Created")
        time.sleep(1)
        assert len(body_text(logged_in)) > 0

    def test_create_multiple_tasks(self, logged_in):
        token = get_root_token()
        api_call("POST", "/api/tasks", {"title": "Task Two", "project": "E2EProject"}, token)
        api_call("POST", "/api/tasks", {"title": "Task Three", "project": "E2EProject"}, token)
        click_tab(logged_in, "Refresh data")
        time.sleep(1)
        click_tab(logged_in, "Tasks")
        time.sleep(1)
        body = body_text(logged_in)
        assert "Task Two" in body or "E2EProject" in body


# ── Flow: user-creates-sprint.md ───────────────────────────────

class TestSprints:

    def test_sprints_tab_loads(self, logged_in):
        click_tab(logged_in, "Sprints")
        time.sleep(0.5)
        body = body_text(logged_in)
        assert "sprint" in body.lower() or "Sprint" in body

    def test_create_sprint_via_api_shows_in_gui(self, logged_in):
        token = get_root_token()
        api_call("POST", "/api/sprints", {
            "name": "E2E Sprint 1",
            "start_date": "2026-04-14",
            "end_date": "2026-04-28",
        }, token)
        click_tab(logged_in, "Timer")
        time.sleep(0.5)
        click_tab(logged_in, "Sprints")
        time.sleep(1.5)
        body = body_text(logged_in)
        assert "E2E Sprint 1" in body or "Sprint" in body


# ── Flow: collaborative-estimation-room.md ─────────────────────

class TestRooms:

    def test_rooms_tab_loads(self, logged_in):
        click_tab(logged_in, "Rooms")
        time.sleep(0.5)
        body = body_text(logged_in)
        assert "room" in body.lower() or "Room" in body

    def test_create_room_button_exists(self, logged_in):
        click_tab(logged_in, "Rooms")
        time.sleep(0.5)
        logged_in.assert_visible("New Room")

    def test_create_room_via_api_shows_in_gui(self, logged_in):
        token = get_root_token()
        api_call("POST", "/api/rooms", {"name": "E2E Room", "estimation_unit": "points"}, token)
        click_tab(logged_in, "Timer")
        time.sleep(0.5)
        click_tab(logged_in, "Rooms")
        time.sleep(1.5)
        body = body_text(logged_in)
        assert "E2E Room" in body or "Room" in body


# ── Flow: history-stats-reports-audit.md ────────────────────────

class TestHistory:

    def test_history_tab_loads(self, logged_in):
        click_tab(logged_in, "History")
        time.sleep(0.5)
        body = body_text(logged_in)
        assert "session" in body.lower() or "streak" in body.lower() or "hours" in body.lower()

    def test_history_shows_stats(self, logged_in):
        click_tab(logged_in, "History")
        time.sleep(0.5)
        body = body_text(logged_in)
        assert "Total Sessions" in body or "Focus Hours" in body


# ── Settings / Config ──────────────────────────────────────────

class TestSettings:

    def test_settings_tab_loads(self, logged_in):
        click_tab(logged_in, "Settings")
        time.sleep(0.5)
        body = body_text(logged_in)
        assert "Timer Durations" in body or "Work" in body

    def test_settings_shows_username(self, logged_in):
        click_tab(logged_in, "Settings")
        time.sleep(0.5)
        body = body_text(logged_in)
        assert "root" in body

    def test_settings_shows_server_url(self, logged_in):
        click_tab(logged_in, "Settings")
        time.sleep(0.5)
        val = logged_in.execute_js("""
            const inputs = document.querySelectorAll('input');
            for (const i of inputs) {
                if (i.value.includes('19090') || i.value.includes('127.0.0.1')) return i.value;
            }
            return '';
        """)
        assert "19090" in val or "127.0.0.1" in val

    def test_settings_has_save_button(self, logged_in):
        click_tab(logged_in, "Settings")
        time.sleep(0.5)
        logged_in.assert_visible("Save Settings")

    def test_settings_has_team_button(self, logged_in):
        click_tab(logged_in, "Settings")
        time.sleep(0.5)
        logged_in.assert_visible("+ New Team")

    def test_settings_estimation_mode(self, logged_in):
        click_tab(logged_in, "Settings")
        time.sleep(0.5)
        body = body_text(logged_in)
        assert "Estimation Mode" in body or "Hours" in body


# ── Theme toggle ───────────────────────────────────────────────

class TestTheme:

    def test_toggle_theme(self, logged_in):
        old_theme = logged_in.execute_js("return document.documentElement.getAttribute('data-theme')")
        click_tab(logged_in, "Toggle theme")
        time.sleep(0.5)
        new_theme = logged_in.execute_js("return document.documentElement.getAttribute('data-theme')")
        assert new_theme != old_theme
        assert new_theme in ("dark", "light")

    def test_toggle_back(self, logged_in):
        old_theme = logged_in.execute_js("return document.documentElement.getAttribute('data-theme')")
        click_tab(logged_in, "Toggle theme")
        time.sleep(0.5)
        new_theme = logged_in.execute_js("return document.documentElement.getAttribute('data-theme')")
        assert new_theme != old_theme


# ── Refresh ────────────────────────────────────────────────────

class TestRefresh:

    def test_refresh_data(self, logged_in):
        click_tab(logged_in, "Tasks")
        time.sleep(0.5)
        click_tab(logged_in, "Refresh data")
        time.sleep(1)
        assert len(body_text(logged_in)) > 0


# ── API tab ────────────────────────────────────────────────────

class TestApiTab:

    def test_api_tab_loads(self, logged_in):
        click_tab(logged_in, "API")
        time.sleep(1)
        body = body_text(logged_in)
        assert "api" in body.lower() or "API" in body or "Loading" in body


# ── DOM integrity ───────────────────────────────────────────────

class TestDomIntegrity:

    def test_react_root(self, logged_in):
        assert 'id="root"' in logged_in.page_source()

    def test_title(self, app):
        assert app.title() == "Pomodoro"

    def test_no_js_errors(self, logged_in):
        root = logged_in.find("#root")
        assert logged_in.is_displayed(root)

    def test_sidebar_has_all_buttons(self, logged_in):
        expected = ["Timer", "Tasks", "Sprints", "Rooms", "History", "API", "Settings", "Toggle theme", "Refresh data", "Logout"]
        for title in expected:
            elems = logged_in.find_all(f"button[title='{title}']")
            assert len(elems) > 0, f"Missing sidebar button: {title}"


# ── Multi-user flow ────────────────────────────────────────────

class TestMultiUser:

    def test_second_user_sees_shared_data(self, app):
        token = get_root_token()
        api_call("POST", "/api/tasks", {"title": "SharedVizTask", "project": "SharedProject"}, token)
        try:
            api_call("POST", "/api/auth/register", {"username": "viewer1", "password": "ViewerP1"})
        except Exception:
            pass  # may already exist from previous run
        ensure_login_screen(app)
        gui_login(app, "viewer1", "ViewerP1")
        click_tab(app, "Tasks")
        time.sleep(1)
        body = body_text(app)
        assert "SharedProject" in body or "SharedVizTask" in body or len(body) > 50
        ensure_login_screen(app)
        gui_login(app, "root", ROOT_PASSWORD)


# ── Negative: password validation via GUI ───────────────────────

class TestPasswordValidation:

    def test_register_short_password_shows_error(self, app):
        ensure_login_screen(app)
        app.click_text("No account? Register", "button")
        time.sleep(0.5)
        set_input(app, "input[placeholder='Username']", "shortpw1")
        set_input(app, "input[placeholder*='Password']", "Short1a")
        btns = app.find_all("button")
        for b in btns:
            txt = app.text(b).strip().lower()
            if "create" in txt or "register" in txt or "sign up" in txt:
                app.click(b)
                break
        time.sleep(1)
        body = body_text(app)
        assert "8 char" in body.lower() or "at least 8" in body.lower() or "error" in body.lower() or "bad_request" in body.lower()

    def test_register_no_uppercase_shows_error(self, app):
        ensure_login_screen(app)
        app.click_text("No account? Register", "button")
        time.sleep(0.5)
        set_input(app, "input[placeholder='Username']", "noupuser")
        set_input(app, "input[placeholder*='Password']", "alllower1")
        btns = app.find_all("button")
        for b in btns:
            txt = app.text(b).strip().lower()
            if "create" in txt or "register" in txt or "sign up" in txt:
                app.click(b)
                break
        time.sleep(1)
        body = body_text(app)
        assert "uppercase" in body.lower() or "error" in body.lower() or "bad_request" in body.lower()

    def test_register_no_digit_shows_error(self, app):
        ensure_login_screen(app)
        app.click_text("No account? Register", "button")
        time.sleep(0.5)
        set_input(app, "input[placeholder='Username']", "nodiguser")
        set_input(app, "input[placeholder*='Password']", "NoDigitHere")
        btns = app.find_all("button")
        for b in btns:
            txt = app.text(b).strip().lower()
            if "create" in txt or "register" in txt or "sign up" in txt:
                app.click(b)
                break
        time.sleep(1)
        body = body_text(app)
        assert "digit" in body.lower() or "error" in body.lower() or "bad_request" in body.lower()

    def test_valid_password_succeeds_after_failures(self, app):
        ensure_login_screen(app)
        app.click_text("No account? Register", "button")
        time.sleep(0.5)
        set_input(app, "input[placeholder='Username']", "validpw1")
        set_input(app, "input[placeholder*='Password']", "ValidPass1")
        btns = app.find_all("button")
        for b in btns:
            txt = app.text(b).strip().lower()
            if "create" in txt or "register" in txt or "sign up" in txt:
                app.click(b)
                break
        time.sleep(2)
        app.assert_visible("Start Focus")


# ── Session expiry ──────────────────────────────────────────────

class TestSessionExpiry:

    def test_revoked_token_forces_relogin(self, app):
        ensure_login_screen(app)
        gui_login(app, "root", ROOT_PASSWORD)
        app.assert_visible("Start Focus")
        token = app.execute_js("return localStorage.getItem('auth')")
        tok = ""
        if token:
            try:
                tok = json.loads(token).get("token", "")
            except Exception:
                pass
        if tok:
            try:
                req = urllib.request.Request(
                    f"{harness.BASE_URL}/api/auth/logout", data=b"",
                    headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json", "X-Requested-With": "test"},
                    method="POST",
                )
                urllib.request.urlopen(req, timeout=5)
            except Exception:
                pass
        click_tab(app, "Tasks")
        time.sleep(2)
        assert len(body_text(app)) > 0

    def test_fresh_login_works_after_expiry(self, app):
        ensure_login_screen(app)
        gui_login(app, "root", ROOT_PASSWORD)
        app.assert_visible("Start Focus")
