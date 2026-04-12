"""Sprint lifecycle E2E tests: create via API, verify + interact via GUI."""

import time
import json
import urllib.request
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


def click_sprint(app, name):
    app.execute_js(f"""
        var divs = document.querySelectorAll('div');
        for (var i = 0; i < divs.length; i++) {{
            if (divs[i].textContent.includes('{name}') && divs[i].className.indexOf('cursor-pointer') >= 0) {{
                divs[i].click(); break;
            }}
        }}
    """)
    time.sleep(1)


def navigate_to_sprint(app, name):
    click_tab(app, "Refresh data")
    time.sleep(0.5)
    click_tab(app, "Sprints")
    click_sprint(app, name)


# Use a unique name per test run to avoid collisions
import os
_RUN_ID = os.getpid()
SPRINT_NAME = f"Sprint_{_RUN_ID}"


@pytest.fixture(scope="module")
def sprint_data(daemon):
    token = root_token()
    t1 = api("POST", "/api/tasks", {"title": "ST1", "project": "SP"}, token)
    t2 = api("POST", "/api/tasks", {"title": "ST2", "project": "SP"}, token)
    sprint = api("POST", "/api/sprints", {
        "name": SPRINT_NAME,
        "start_date": "2026-04-14",
        "end_date": "2026-04-28",
    }, token)
    api("POST", f"/api/sprints/{sprint['id']}/tasks",
        {"task_ids": [t1["id"], t2["id"]]}, token)
    return {"id": sprint["id"]}


class TestSprintDisplay:

    def test_sprint_visible_in_list(self, logged_in, sprint_data):
        click_tab(logged_in, "Refresh data")
        time.sleep(0.5)
        click_tab(logged_in, "Sprints")
        assert SPRINT_NAME in logged_in.page_source()

    def test_sprint_shows_planning_status(self, logged_in, sprint_data):
        click_tab(logged_in, "Sprints")
        assert "planning" in logged_in.page_source()

    def test_sprint_detail_shows_board(self, logged_in, sprint_data):
        click_tab(logged_in, "Sprints")
        click_sprint(logged_in, SPRINT_NAME)
        body = body_text(logged_in)
        assert "Board" in body or "Todo" in body


class TestSprintLifecycle:

    def test_start_sprint(self, logged_in, sprint_data):
        token = root_token()
        api("POST", f"/api/sprints/{sprint_data['id']}/start", token=token)
        navigate_to_sprint(logged_in, SPRINT_NAME)
        body = body_text(logged_in)
        assert "Complete" in body or "active" in body.lower()

    def test_active_sprint_has_columns(self, logged_in, sprint_data):
        navigate_to_sprint(logged_in, SPRINT_NAME)
        body = body_text(logged_in)
        assert "Todo" in body and "In Progress" in body and "Done" in body

    def test_complete_sprint(self, logged_in, sprint_data):
        token = root_token()
        api("POST", f"/api/sprints/{sprint_data['id']}/complete", token=token)
        navigate_to_sprint(logged_in, SPRINT_NAME)
        assert "completed" in logged_in.page_source()

    def test_completed_sprint_in_list(self, logged_in, sprint_data):
        click_tab(logged_in, "Sprints")
        src = logged_in.page_source()
        assert SPRINT_NAME in src
        assert "completed" in src
