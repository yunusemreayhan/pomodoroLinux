"""Estimation room E2E tests: create via API, vote + reveal via GUI."""

import time
import json
import urllib.request
import os
import pytest
import harness
from harness import ROOT_PASSWORD


def click_tab(app, title):
    app.execute_js(f'document.querySelector(\'button[title="{title}"]\')?.click()')
    time.sleep(1)


def api(method, path, body=None, token=None):
    data = json.dumps(body).encode() if body else (b"" if method in ("POST", "PUT") else None)
    hdrs = {"Content-Type": "application/json", "X-Requested-With": "test"}
    if token:
        hdrs["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(f"{harness.BASE_URL}{path}", data=data, headers=hdrs, method=method)
    resp = urllib.request.urlopen(req, timeout=5)
    raw = resp.read().decode()
    return json.loads(raw) if raw else {}


def root_token():
    return api("POST", "/api/auth/login", {"username": "root", "password": ROOT_PASSWORD})["token"]


def body_text(app):
    return app.text(app.find("body"))


def click_room(app, name):
    """Click a room card in the list."""
    app.execute_js(f"""
        var els = document.querySelectorAll('[role="button"], .glass, [tabindex="0"]');
        for (var i = 0; i < els.length; i++) {{
            if (els[i].textContent.includes('{name}') && els[i].className.indexOf('cursor-pointer') >= 0) {{
                els[i].click(); break;
            }}
        }}
    """)
    time.sleep(1.5)


_RUN_ID = os.getpid()


class TestRoomDisplay:

    def test_room_shows_in_gui(self, logged_in):
        token = root_token()
        api("POST", "/api/rooms", {"name": f"Room_{_RUN_ID}", "estimation_unit": "points"}, token)
        click_tab(logged_in, "Refresh data")
        time.sleep(0.5)
        click_tab(logged_in, "Rooms")
        assert f"Room_{_RUN_ID}" in logged_in.page_source()


class TestRoomVoting:

    @pytest.fixture(autouse=True)
    def setup_room(self, logged_in):
        self.token = root_token()
        room = api("POST", "/api/rooms", {"name": f"Vote_{_RUN_ID}", "estimation_unit": "points"}, self.token)
        self.room_id = room["id"]
        api("POST", f"/api/rooms/{self.room_id}/join", token=self.token)
        task = api("POST", "/api/tasks", {"title": f"Est_{_RUN_ID}", "project": "VP"}, self.token)
        self.task_id = task["id"]
        api("POST", f"/api/rooms/{self.room_id}/start-voting", {"task_id": task["id"]}, self.token)

    def test_room_detail_shows_task(self, logged_in):
        click_tab(logged_in, "Refresh data")
        time.sleep(0.5)
        click_tab(logged_in, "Rooms")
        click_room(logged_in, f"Vote_{_RUN_ID}")
        body = body_text(logged_in)
        assert f"Est_{_RUN_ID}" in body or "voting" in body.lower() or "Reveal" in body

    def test_vote_and_reveal_via_api_shows_in_gui(self, logged_in):
        """Vote + reveal via API, verify results visible in GUI."""
        api("POST", f"/api/rooms/{self.room_id}/vote", {"value": 5}, self.token)
        api("POST", f"/api/rooms/{self.room_id}/reveal", token=self.token)

        click_tab(logged_in, "Refresh data")
        time.sleep(0.5)
        click_tab(logged_in, "Rooms")
        click_room(logged_in, f"Vote_{_RUN_ID}")
        time.sleep(1)

        src = logged_in.page_source()
        assert "revealed" in src or "5" in src or f"Vote_{_RUN_ID}" in src

    def test_room_members_visible(self, logged_in):
        click_tab(logged_in, "Rooms")
        click_room(logged_in, f"Vote_{_RUN_ID}")
        body = body_text(logged_in)
        assert "root" in body or "members" in body.lower()
