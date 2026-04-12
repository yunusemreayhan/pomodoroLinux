"""Task CRUD E2E tests: create/edit/delete via API, verify via GUI."""

import time
import json
import os
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


def refresh_tasks(app):
    click_tab(app, "Refresh data")
    time.sleep(0.5)
    click_tab(app, "Tasks")
    time.sleep(1)


_RUN_ID = os.getpid()


class TestTaskCreate:

    def test_api_task_shows_in_gui(self, logged_in):
        token = root_token()
        api("POST", "/api/tasks", {"title": f"Task_{_RUN_ID}", "project": f"Proj_{_RUN_ID}"}, token)
        refresh_tasks(logged_in)
        assert f"Task_{_RUN_ID}" in logged_in.page_source()

    def test_multiple_projects(self, logged_in):
        token = root_token()
        api("POST", "/api/tasks", {"title": "PA1", "project": f"ProjA_{_RUN_ID}"}, token)
        api("POST", "/api/tasks", {"title": "PB1", "project": f"ProjB_{_RUN_ID}"}, token)
        refresh_tasks(logged_in)
        src = logged_in.page_source()
        assert f"ProjA_{_RUN_ID}" in src
        assert f"ProjB_{_RUN_ID}" in src


class TestTaskEdit:

    def test_rename_reflects_in_gui(self, logged_in):
        token = root_token()
        task = api("POST", "/api/tasks", {"title": f"Old_{_RUN_ID}", "project": "Edit"}, token)
        refresh_tasks(logged_in)
        assert f"Old_{_RUN_ID}" in logged_in.page_source()

        api("PUT", f"/api/tasks/{task['id']}", {"title": f"New_{_RUN_ID}"}, token)
        refresh_tasks(logged_in)
        src = logged_in.page_source()
        assert f"New_{_RUN_ID}" in src

    def test_status_change(self, logged_in):
        token = root_token()
        task = api("POST", "/api/tasks", {"title": f"Stat_{_RUN_ID}", "project": "Edit"}, token)
        api("PUT", f"/api/tasks/{task['id']}", {"status": "completed"}, token)
        # Verify via API
        tasks = api("GET", "/api/tasks", token=token)
        t = next(t for t in tasks if t["id"] == task["id"])
        assert t["status"] == "completed"


class TestTaskDelete:

    def test_soft_delete_removes_from_gui(self, logged_in):
        token = root_token()
        task = api("POST", "/api/tasks", {"title": f"Del_{_RUN_ID}", "project": f"DelP_{_RUN_ID}"}, token)
        refresh_tasks(logged_in)
        assert f"Del_{_RUN_ID}" in logged_in.page_source()

        api("DELETE", f"/api/tasks/{task['id']}", token=token)
        refresh_tasks(logged_in)
        assert f"Del_{_RUN_ID}" not in logged_in.page_source()

    def test_restore_reappears_in_gui(self, logged_in):
        token = root_token()
        task = api("POST", "/api/tasks", {"title": f"Res_{_RUN_ID}", "project": f"ResP_{_RUN_ID}"}, token)
        api("DELETE", f"/api/tasks/{task['id']}", token=token)
        refresh_tasks(logged_in)
        assert f"Res_{_RUN_ID}" not in logged_in.page_source()

        api("POST", f"/api/tasks/{task['id']}/restore", token=token)
        refresh_tasks(logged_in)
        assert f"Res_{_RUN_ID}" in logged_in.page_source()

    def test_purge_gone_permanently(self, logged_in):
        token = root_token()
        task = api("POST", "/api/tasks", {"title": f"Purge_{_RUN_ID}", "project": "Purge"}, token)
        api("DELETE", f"/api/tasks/{task['id']}", token=token)
        api("DELETE", f"/api/tasks/{task['id']}/purge", token=token)
        deleted = api("GET", "/api/tasks/deleted", token=token)
        assert not any(t["title"] == f"Purge_{_RUN_ID}" for t in deleted)

    def test_bulk_status_update(self, logged_in):
        token = root_token()
        t1 = api("POST", "/api/tasks", {"title": "B1", "project": "Bulk"}, token)
        t2 = api("POST", "/api/tasks", {"title": "B2", "project": "Bulk"}, token)
        api("POST", "/api/tasks/bulk-status",
            {"task_ids": [t1["id"], t2["id"]], "status": "completed"}, token)
        tasks = api("GET", "/api/tasks", token=token)
        bulk = [t for t in tasks if t["id"] in (t1["id"], t2["id"])]
        assert all(t["status"] == "completed" for t in bulk)
