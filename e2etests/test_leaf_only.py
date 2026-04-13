"""Test leaf_only_mode: when enabled, task listing should exclude parent tasks (tasks with children)."""

import json, os, urllib.request, urllib.error
import pytest

# Standalone daemon fixture (no GUI needed)
@pytest.fixture(scope="module")
def daemon():
    import harness
    d = harness.Daemon()
    d.start()
    yield d
    d.stop()


def api(method, path, body=None, token=None, base_url=None):
    url = base_url or os.environ.get("POMODORO_TEST_URL", "http://127.0.0.1:9090")
    data = json.dumps(body).encode() if body is not None else (b"" if method in ("POST", "PUT") else None)
    hdrs = {"Content-Type": "application/json", "X-Requested-With": "test"}
    if token:
        hdrs["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(f"{url}{path}", data=data, headers=hdrs, method=method)
    try:
        resp = urllib.request.urlopen(req, timeout=10)
        raw = resp.read().decode()
        return resp.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        try:
            return e.code, json.loads(raw)
        except Exception:
            return e.code, {"error": raw}


def login(base_url, user="root", pw=None):
    pw = pw or os.environ.get("POMODORO_ROOT_PASSWORD", "TestRoot1")
    status, body = api("POST", "/api/auth/login", {"username": user, "password": pw}, base_url=base_url)
    assert status == 200, f"Login failed: {body}"
    return body["token"]


class TestLeafOnlyMode:
    """When leaf_only_mode is ON, GET /api/tasks should only return leaf tasks (no children).
    When OFF, all tasks should be returned."""

    @pytest.fixture(autouse=True)
    def setup(self, daemon):
        self.url = daemon.base_url
        self.token = login(self.url)

        # Create parent task
        _, self.parent = api("POST", "/api/tasks", {"title": "Parent Task"}, self.token, self.url)
        # Create child task under parent
        _, self.child = api("POST", "/api/tasks", {"title": "Child Task", "parent_id": self.parent["id"]}, self.token, self.url)
        # Create standalone leaf task (no children)
        _, self.leaf = api("POST", "/api/tasks", {"title": "Standalone Leaf"}, self.token, self.url)

    def _set_leaf_only(self, enabled):
        status, cfg = api("GET", "/api/config", token=self.token, base_url=self.url)
        assert status == 200
        cfg["leaf_only_mode"] = enabled
        status, result = api("PUT", "/api/config", cfg, self.token, self.url)
        assert status == 200
        assert result["leaf_only_mode"] == enabled

    def _get_task_ids(self, endpoint="/api/tasks"):
        status, resp = api("GET", endpoint, token=self.token, base_url=self.url)
        assert status == 200
        tasks = resp["tasks"] if "tasks" in resp else resp
        return [t["id"] for t in tasks]

    def test_leaf_only_off_returns_all_tasks(self):
        """With leaf_only_mode OFF, all tasks (parent + child + leaf) should appear."""
        self._set_leaf_only(False)
        ids = self._get_task_ids()
        assert self.parent["id"] in ids, "Parent should be visible when leaf_only_mode is OFF"
        assert self.child["id"] in ids, "Child should be visible when leaf_only_mode is OFF"
        assert self.leaf["id"] in ids, "Standalone leaf should be visible when leaf_only_mode is OFF"

    def test_leaf_only_on_excludes_parents(self):
        """With leaf_only_mode ON, API still returns all tasks (filtering is GUI-side)."""
        self._set_leaf_only(True)
        ids = self._get_task_ids()
        assert self.parent["id"] in ids, "API should return parent even with leaf_only ON"
        assert self.child["id"] in ids
        assert self.leaf["id"] in ids

    def test_leaf_only_toggle_back(self):
        """Config toggle persists correctly."""
        self._set_leaf_only(True)
        status, cfg = api("GET", "/api/config", token=self.token, base_url=self.url)
        assert cfg["leaf_only_mode"] is True

        self._set_leaf_only(False)
        status, cfg = api("GET", "/api/config", token=self.token, base_url=self.url)
        assert cfg["leaf_only_mode"] is False

    def test_tasks_full_leaf_only_off(self):
        """/api/tasks/full returns all tasks regardless of leaf_only."""
        self._set_leaf_only(False)
        ids = self._get_task_ids("/api/tasks/full")
        assert self.parent["id"] in ids
        assert self.child["id"] in ids
        assert self.leaf["id"] in ids

    def test_tasks_full_leaf_only_on(self):
        """/api/tasks/full returns all tasks even with leaf_only ON (filtering is GUI-side)."""
        self._set_leaf_only(True)
        ids = self._get_task_ids("/api/tasks/full")
        assert self.parent["id"] in ids, "API should return parent — GUI does the filtering"
        assert self.child["id"] in ids
        assert self.leaf["id"] in ids

    def test_parent_id_present_in_response(self):
        """Tasks include parent_id so GUI can build ancestor breadcrumbs."""
        self._set_leaf_only(False)
        status, resp = api("GET", "/api/tasks/full", token=self.token, base_url=self.url)
        tasks = resp["tasks"]
        child = next(t for t in tasks if t["id"] == self.child["id"])
        assert child["parent_id"] == self.parent["id"], "Child should reference parent_id for breadcrumb"
