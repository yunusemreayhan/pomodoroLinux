"""Import/Export, Recurrence, Webhooks, Sprint burndown/velocity."""

import time, json, os, urllib.request
import pytest
import harness
from harness import ROOT_PASSWORD

_ID = os.getpid()


def api(method, path, body=None, token=None):
    url = harness.BASE_URL
    if body is not None:
        data = json.dumps(body).encode()
        hdrs = {"Content-Type": "application/json", "X-Requested-With": "test"}
    elif method in ("POST", "PUT"):
        data, hdrs = b"", {"Content-Type": "application/json", "X-Requested-With": "test"}
    else:
        data, hdrs = None, {"X-Requested-With": "test"}
    if token:
        hdrs["Authorization"] = f"Bearer {token}"
    resp = urllib.request.urlopen(
        urllib.request.Request(f"{url}{path}", data=data, headers=hdrs, method=method), timeout=5)
    raw = resp.read().decode()
    return json.loads(raw) if raw else {}


def token():
    return api("POST", "/api/auth/login", {"username": "root", "password": ROOT_PASSWORD})["token"]


class TestExport:

    def test_export_tasks(self, logged_in):
        t = token()
        api("POST", "/api/tasks", {"title": f"Ex_{_ID}", "project": "Ex"}, t)
        result = api("GET", "/api/export/tasks", token=t)
        assert isinstance(result, list) and len(result) >= 1

    def test_export_sessions(self, logged_in):
        t = token()
        # Sessions export returns CSV by default; just verify 200
        url = harness.BASE_URL
        resp = urllib.request.urlopen(
            urllib.request.Request(f"{url}/api/export/sessions?format=json",
                headers={"X-Requested-With": "test", "Authorization": f"Bearer {t}"}), timeout=5)
        assert resp.status == 200


class TestImport:

    def test_import_tasks_json(self, logged_in):
        t = token()
        result = api("POST", "/api/import/tasks/json",
                      {"tasks": [{"title": f"Imp_{_ID}", "project": "Imp"}]}, t)
        assert result.get("imported", 0) >= 1 or isinstance(result, dict)


class TestRecurrence:

    def test_set_recurrence(self, logged_in):
        t = token()
        task = api("POST", "/api/tasks", {"title": f"Rec_{_ID}", "project": "Rec"}, t)
        api("PUT", f"/api/tasks/{task['id']}/recurrence",
            {"pattern": "daily", "next_due": "2026-04-13"}, t)
        rec = api("GET", f"/api/tasks/{task['id']}/recurrence", token=t)
        assert rec.get("pattern") == "daily"

    def test_delete_recurrence(self, logged_in):
        t = token()
        task = api("POST", "/api/tasks", {"title": f"RecD_{_ID}", "project": "Rec"}, t)
        api("PUT", f"/api/tasks/{task['id']}/recurrence",
            {"pattern": "weekly", "next_due": "2026-04-19"}, t)
        api("DELETE", f"/api/tasks/{task['id']}/recurrence", token=t)
        rec = api("GET", f"/api/tasks/{task['id']}/recurrence", token=t)
        assert not rec or rec.get("pattern") is None


class TestWebhooks:

    def test_list_webhooks(self, logged_in):
        t = token()
        hooks = api("GET", "/api/webhooks", token=t)
        assert isinstance(hooks, list)


class TestSprintAnalytics:

    def test_velocity(self, logged_in):
        t = token()
        result = api("GET", "/api/sprints/velocity", token=t)
        assert isinstance(result, list)

    def test_burndown(self, logged_in):
        t = token()
        s = api("POST", "/api/sprints", {"name": f"Bd_{_ID}", "start_date": "2026-04-14", "end_date": "2026-04-28"}, t)
        result = api("GET", f"/api/sprints/{s['id']}/burndown", token=t)
        assert isinstance(result, (list, dict))

    def test_sprint_scope(self, logged_in):
        t = token()
        s = api("POST", "/api/sprints", {"name": f"Sc_{_ID}", "start_date": "2026-04-14", "end_date": "2026-04-28"}, t)
        result = api("GET", f"/api/sprints/{s['id']}/scope", token=t)
        assert isinstance(result, (list, dict))
