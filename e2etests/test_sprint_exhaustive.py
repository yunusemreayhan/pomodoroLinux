"""Exhaustive sprint tests: every endpoint, lifecycle, burns, tasks, analytics."""

import time, json, os, urllib.request
import pytest
import harness
from harness import ROOT_PASSWORD

_ID = os.getpid()
_tok = {}


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


def api_err(method, path, body=None, token=None):
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
    try:
        urllib.request.urlopen(
            urllib.request.Request(f"{url}{path}", data=data, headers=hdrs, method=method), timeout=5)
        return 200, ""
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:300]


def tok():
    if "root" not in _tok:
        _tok["root"] = api("POST", "/api/auth/login", {"username": "root", "password": ROOT_PASSWORD})["token"]
    return _tok["root"]


def make_sprint(name, **kw):
    body = {"name": name, "start_date": "2026-05-01", "end_date": "2026-05-15"}
    body.update(kw)
    return api("POST", "/api/sprints", body, tok())


class TestSprintCreate:

    def test_minimal(self, logged_in):
        s = api("POST", "/api/sprints", {"name": f"Sm_{_ID}"}, tok())
        assert s["name"] == f"Sm_{_ID}"

    def test_with_dates(self, logged_in):
        s = make_sprint(f"Sd_{_ID}")
        assert s["start_date"] and s["end_date"]

    def test_with_project(self, logged_in):
        s = make_sprint(f"Sp_{_ID}", project="MyProj")
        assert s.get("project") == "MyProj"

    def test_with_goal(self, logged_in):
        s = make_sprint(f"Sg_{_ID}", goal="Ship v2")
        assert s.get("goal") == "Ship v2"

    def test_with_capacity(self, logged_in):
        s = make_sprint(f"Sc_{_ID}", capacity_hours=40.0)
        assert s.get("capacity_hours") == 40.0


class TestSprintUpdate:

    def test_update_name(self, logged_in):
        s = make_sprint(f"Su_{_ID}")
        r = api("PUT", f"/api/sprints/{s['id']}", {"name": "Renamed"}, tok())
        assert r["name"] == "Renamed"

    def test_update_goal(self, logged_in):
        s = make_sprint(f"Sug_{_ID}")
        r = api("PUT", f"/api/sprints/{s['id']}", {"goal": "New goal"}, tok())
        assert r.get("goal") == "New goal"

    def test_delete_sprint(self, logged_in):
        s = make_sprint(f"Sdel_{_ID}")
        api("DELETE", f"/api/sprints/{s['id']}", token=tok())
        sprints = api("GET", "/api/sprints", token=tok())
        assert not any(x["id"] == s["id"] for x in sprints)


class TestSprintTasks:

    def test_add_tasks(self, logged_in):
        s = make_sprint(f"St_{_ID}")
        t1 = api("POST", "/api/tasks", {"title": "ST1"}, tok())
        t2 = api("POST", "/api/tasks", {"title": "ST2"}, tok())
        api("POST", f"/api/sprints/{s['id']}/tasks", {"task_ids": [t1["id"], t2["id"]]}, tok())
        tasks = api("GET", f"/api/sprints/{s['id']}/tasks", token=tok())
        ids = [t["id"] for t in tasks]
        assert t1["id"] in ids and t2["id"] in ids

    def test_remove_task(self, logged_in):
        s = make_sprint(f"Str_{_ID}")
        t = api("POST", "/api/tasks", {"title": "STR"}, tok())
        api("POST", f"/api/sprints/{s['id']}/tasks", {"task_ids": [t["id"]]}, tok())
        api("DELETE", f"/api/sprints/{s['id']}/tasks/{t['id']}", token=tok())
        tasks = api("GET", f"/api/sprints/{s['id']}/tasks", token=tok())
        assert not any(x["id"] == t["id"] for x in tasks)


class TestSprintRoots:

    def test_add_root(self, logged_in):
        s = make_sprint(f"Sr_{_ID}")
        t = api("POST", "/api/tasks", {"title": "Root"}, tok())
        api("POST", f"/api/sprints/{s['id']}/roots", {"task_ids": [t["id"]]}, tok())
        roots = api("GET", f"/api/sprints/{s['id']}/roots", token=tok())
        assert t["id"] in roots

    def test_remove_root(self, logged_in):
        s = make_sprint(f"Srr_{_ID}")
        t = api("POST", "/api/tasks", {"title": "Root2"}, tok())
        api("POST", f"/api/sprints/{s['id']}/roots", {"task_ids": [t["id"]]}, tok())
        api("DELETE", f"/api/sprints/{s['id']}/roots/{t['id']}", token=tok())
        roots = api("GET", f"/api/sprints/{s['id']}/roots", token=tok())
        assert t["id"] not in roots


class TestSprintBurns:

    def test_log_burn(self, logged_in):
        s = make_sprint(f"Sb_{_ID}")
        t = api("POST", "/api/tasks", {"title": "Burn"}, tok())
        api("POST", f"/api/sprints/{s['id']}/tasks", {"task_ids": [t["id"]]}, tok())
        api("POST", f"/api/sprints/{s['id']}/start", token=tok())
        b = api("POST", f"/api/sprints/{s['id']}/burn",
                {"task_id": t["id"], "points": 3.0, "hours": 1.5}, tok())
        assert b["points"] == 3.0

    def test_list_burns(self, logged_in):
        s = make_sprint(f"Sbl_{_ID}")
        api("POST", f"/api/sprints/{s['id']}/start", token=tok())
        burns = api("GET", f"/api/sprints/{s['id']}/burns", token=tok())
        assert isinstance(burns, list)

    def test_burn_summary(self, logged_in):
        s = make_sprint(f"Sbs_{_ID}")
        api("POST", f"/api/sprints/{s['id']}/start", token=tok())
        summary = api("GET", f"/api/sprints/{s['id']}/burn-summary", token=tok())
        assert isinstance(summary, list)

    def test_delete_burn(self, logged_in):
        s = make_sprint(f"Sbd_{_ID}")
        t = api("POST", "/api/tasks", {"title": "BurnDel"}, tok())
        api("POST", f"/api/sprints/{s['id']}/tasks", {"task_ids": [t["id"]]}, tok())
        api("POST", f"/api/sprints/{s['id']}/start", token=tok())
        b = api("POST", f"/api/sprints/{s['id']}/burn",
                {"task_id": t["id"], "points": 1.0}, tok())
        api("DELETE", f"/api/sprints/{s['id']}/burns/{b['id']}", token=tok())


class TestSprintAnalytics:

    def test_detail(self, logged_in):
        s = make_sprint(f"Sdet_{_ID}")
        d = api("GET", f"/api/sprints/{s['id']}", token=tok())
        assert d["sprint"]["name"] == f"Sdet_{_ID}"

    def test_board(self, logged_in):
        s = make_sprint(f"Sbo_{_ID}")
        b = api("GET", f"/api/sprints/{s['id']}/board", token=tok())
        assert isinstance(b, dict)

    def test_burndown(self, logged_in):
        s = make_sprint(f"Sbdn_{_ID}")
        bd = api("GET", f"/api/sprints/{s['id']}/burndown", token=tok())
        assert isinstance(bd, list)

    def test_scope(self, logged_in):
        s = make_sprint(f"Ssc_{_ID}")
        sc = api("GET", f"/api/sprints/{s['id']}/scope", token=tok())
        assert isinstance(sc, list)

    def test_snapshot(self, logged_in):
        s = make_sprint(f"Ssn_{_ID}")
        api("POST", f"/api/sprints/{s['id']}/start", token=tok())
        snap = api("POST", f"/api/sprints/{s['id']}/snapshot", token=tok())
        assert isinstance(snap, dict)

    def test_velocity(self, logged_in):
        v = api("GET", "/api/sprints/velocity", token=tok())
        assert isinstance(v, list)

    def test_global_burndown(self, logged_in):
        bd = api("GET", "/api/sprints/burndown", token=tok())
        assert isinstance(bd, list)

    def test_compare(self, logged_in):
        s1 = make_sprint(f"Cmp1_{_ID}")
        s2 = make_sprint(f"Cmp2_{_ID}")
        c = api("GET", f"/api/sprints/compare?a={s1['id']}&b={s2['id']}", token=tok())
        assert isinstance(c, (list, dict))

    def test_export_burns(self, logged_in):
        s = make_sprint(f"Seb_{_ID}")
        url = harness.BASE_URL
        resp = urllib.request.urlopen(
            urllib.request.Request(f"{url}/api/export/burns/{s['id']}",
                headers={"X-Requested-With": "test", "Authorization": f"Bearer {tok()}"}), timeout=5)
        assert resp.status == 200

    def test_task_sprints(self, logged_in):
        ts = api("GET", "/api/task-sprints", token=tok())
        assert isinstance(ts, list)


class TestSprintCarryover:

    def test_carryover(self, logged_in):
        s = make_sprint(f"Sco_{_ID}")
        t = api("POST", "/api/tasks", {"title": "Carry"}, tok())
        api("POST", f"/api/sprints/{s['id']}/tasks", {"task_ids": [t["id"]]}, tok())
        api("POST", f"/api/sprints/{s['id']}/start", token=tok())
        api("POST", f"/api/sprints/{s['id']}/complete", token=tok())
        new = api("POST", f"/api/sprints/{s['id']}/carryover", token=tok())
        assert new["id"] != s["id"]
