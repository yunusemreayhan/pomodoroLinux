"""E2E test harness: isolated daemon + Tauri GUI via WebDriver.

Spins up a fresh daemon per session, launches the GUI through
tauri-driver, and provides helpers to login/navigate.
"""

from __future__ import annotations

import json
import os
import signal
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import urllib.request
import urllib.error

DAEMON_BINARY = str(
    Path(__file__).resolve().parent.parent / "target" / "release" / "pomodoro-daemon"
)
GUI_BINARY = str(
    Path(__file__).resolve().parent.parent.parent / "pomodoroLinux" / "target" / "release" / "pomodoro-gui"
)
TEST_PORT = 19090
BASE_URL = f"http://127.0.0.1:{TEST_PORT}"
ROOT_PASSWORD = "TestRoot1"
JWT_SECRET = "test-secret-for-flow-tests-1234567890abcdef"


@dataclass
class Daemon:
    """Isolated pomodoro-daemon process."""

    proc: Optional[subprocess.Popen] = None
    tmpdir: Optional[str] = None

    def start(self) -> None:
        self.tmpdir = tempfile.mkdtemp(prefix="pomodoro_e2e_")
        Path(self.tmpdir, "config.toml").write_text(
            f'bind_address = "127.0.0.1"\n'
            f"bind_port = {TEST_PORT}\n"
            f"work_duration_min = 1\n"
            f"short_break_min = 1\n"
            f"long_break_min = 1\n"
            f"long_break_interval = 4\n"
            f"auto_start_breaks = false\n"
            f"auto_start_work = false\n"
            f"sound_enabled = false\n"
            f"notification_enabled = false\n"
            f"daily_goal = 8\n"
        )
        env = os.environ.copy()
        env.update({
            "POMODORO_DATA_DIR": self.tmpdir,
            "POMODORO_CONFIG_DIR": self.tmpdir,
            "POMODORO_JWT_SECRET": JWT_SECRET,
            "POMODORO_ROOT_PASSWORD": ROOT_PASSWORD,
            "POMODORO_SWAGGER": "0",
            "RUST_LOG": "warn",
        })
        self.proc = subprocess.Popen(
            [DAEMON_BINARY], env=env,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            preexec_fn=os.setsid,
        )
        for _ in range(40):
            try:
                urllib.request.urlopen(f"{BASE_URL}/api/health", timeout=1)
                return
            except Exception:
                time.sleep(0.25)
        raise RuntimeError("Daemon failed to start")

    def stop(self) -> None:
        if self.proc:
            os.killpg(os.getpgid(self.proc.pid), signal.SIGTERM)
            self.proc.wait(timeout=5)
            self.proc = None
        if self.tmpdir:
            import shutil
            shutil.rmtree(self.tmpdir, ignore_errors=True)
            self.tmpdir = None


def connect_gui_to_daemon(app):
    """Point the Tauri GUI at the test daemon and reload."""
    app.execute_js(f"""
        localStorage.clear();
        localStorage.setItem('serverUrl', '{BASE_URL}');
        window.__TAURI_INTERNALS__.invoke('set_connection', {{ baseUrl: '{BASE_URL}' }});
    """)
    time.sleep(0.3)
    app.execute_js("location.reload()")
    time.sleep(3)


def gui_login(app, username: str, password: str):
    """Login through the GUI login form."""
    app.execute_js(
        "const nativeSet = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;"
        "const inputs = document.querySelectorAll('input');"
        "nativeSet.call(inputs[0], '" + username + "');"
        "inputs[0].dispatchEvent(new Event('input', { bubbles: true }));"
        "nativeSet.call(inputs[1], '" + password + "');"
        "inputs[1].dispatchEvent(new Event('input', { bubbles: true }));"
    )
    time.sleep(0.3)
    app.click_text("Sign In", "button")
    time.sleep(2)


def gui_logout(app):
    """Logout via the sidebar logout button."""
    try:
        # Logout button is in the sidebar
        app.execute_js("""
            document.querySelectorAll('button').forEach(b => {
                if (b.textContent.includes('Logout') || b.querySelector('[class*="log-out"]'))
                    b.click();
            });
        """)
        time.sleep(1)
    except Exception:
        pass


def gui_register(app, username: str, password: str):
    """Register through the GUI register form."""
    app.click_text("No account? Register", "button")
    time.sleep(0.5)
    app.type_into("input[placeholder='Username']", username)
    app.type_into("input[placeholder*='Password']", password)
    app.click_text("Create Account", "button")
    time.sleep(2)


def api_register(username: str, password: str) -> dict:
    """Register a user via API (faster than GUI for setup)."""
    data = json.dumps({"username": username, "password": password}).encode()
    req = urllib.request.Request(
        f"{BASE_URL}/api/auth/register", data=data,
        headers={"Content-Type": "application/json", "X-Requested-With": "test"},
        method="POST",
    )
    resp = urllib.request.urlopen(req, timeout=5)
    return json.loads(resp.read())
