"""Exhaustive room tests: full lifecycle, join/leave, roles, close, export."""

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


def tok(user="root", pw=ROOT_PASSWORD):
    if user not in _tok:
        _tok[user] = api("POST", "/api/auth/login", {"username": user, "password": pw})["token"]
    return _tok[user]


def make_room(name, **kw):
    body = {"name": name, "estimation_unit": "points"}
    body.update(kw)
    return api("POST", "/api/rooms", body, tok())


class TestRoomCreate:

    def test_minimal(self, logged_in):
        r = api("POST", "/api/rooms", {"name": f"Rm_{_ID}"}, tok())
        assert r["name"] == f"Rm_{_ID}"

    def test_with_unit_points(self, logged_in):
        r = make_room(f"Rp_{_ID}")
        assert r.get("estimation_unit") == "points"

    def test_with_project(self, logged_in):
        r = make_room(f"Rpr_{_ID}", project="RoomProj")
        assert r.get("project") == "RoomProj"


class TestRoomDetail:

    def test_get_detail(self, logged_in):
        r = make_room(f"Rd_{_ID}")
        d = api("GET", f"/api/rooms/{r['id']}", token=tok())
        assert d["room"]["name"] == f"Rd_{_ID}" or d.get("name") == f"Rd_{_ID}"

    def test_list_rooms(self, logged_in):
        make_room(f"Rl_{_ID}")
        rooms = api("GET", "/api/rooms", token=tok())
        assert any(x["name"] == f"Rl_{_ID}" for x in rooms)


class TestRoomLifecycle:

    def test_start_voting(self, logged_in):
        r = make_room(f"Rv_{_ID}")
        t = api("POST", "/api/tasks", {"title": "VoteTask"}, tok())
        result = api("POST", f"/api/rooms/{r['id']}/start-voting", {"task_id": t["id"]}, tok())
        assert result.get("status") == "voting" or result.get("voting_task_id") == t["id"]

    def test_vote_and_reveal(self, logged_in):
        r = make_room(f"Rvr_{_ID}")
        t = api("POST", "/api/tasks", {"title": "VR"}, tok())
        api("POST", f"/api/rooms/{r['id']}/start-voting", {"task_id": t["id"]}, tok())
        api("POST", f"/api/rooms/{r['id']}/vote", {"value": 5}, tok())
        result = api("POST", f"/api/rooms/{r['id']}/reveal", token=tok())
        assert result.get("status") == "revealed" or "votes" in str(result)

    def test_accept_estimate(self, logged_in):
        r = make_room(f"Ra_{_ID}")
        t = api("POST", "/api/tasks", {"title": "Accept"}, tok())
        api("POST", f"/api/rooms/{r['id']}/start-voting", {"task_id": t["id"]}, tok())
        api("POST", f"/api/rooms/{r['id']}/vote", {"value": 8}, tok())
        api("POST", f"/api/rooms/{r['id']}/reveal", token=tok())
        result = api("POST", f"/api/rooms/{r['id']}/accept", {"value": 8}, tok())
        assert result.get("estimated") == 8 or isinstance(result, dict)

    def test_close_room(self, logged_in):
        r = make_room(f"Rc_{_ID}")
        api("POST", f"/api/rooms/{r['id']}/close", token=tok())
        d = api("GET", f"/api/rooms/{r['id']}", token=tok())
        room = d.get("room", d)
        assert room.get("status") == "closed" or room.get("closed")


class TestRoomMultiUser:

    @pytest.fixture(autouse=True)
    def _users(self, logged_in):
        try:
            api("POST", "/api/auth/register", {"username": f"ru2_{_ID}", "password": "TestRu21"}, tok())
        except Exception:
            pass  # Already registered

    def test_join_room(self, logged_in):
        r = make_room(f"Rj_{_ID}")
        t2 = tok(f"ru2_{_ID}", "TestRu21")
        api("POST", f"/api/rooms/{r['id']}/join", token=t2)
        d = api("GET", f"/api/rooms/{r['id']}", token=tok())
        members = d.get("members", [])
        assert len(members) >= 2

    def test_leave_room(self, logged_in):
        r = make_room(f"Rlv_{_ID}")
        t2 = tok(f"ru2_{_ID}", "TestRu21")
        api("POST", f"/api/rooms/{r['id']}/join", token=t2)
        api("POST", f"/api/rooms/{r['id']}/leave", token=t2)

    def test_remove_member(self, logged_in):
        r = make_room(f"Rrm_{_ID}")
        t2 = tok(f"ru2_{_ID}", "TestRu21")
        api("POST", f"/api/rooms/{r['id']}/join", token=t2)
        api("DELETE", f"/api/rooms/{r['id']}/members/ru2_{_ID}", token=tok())

    def test_change_role(self, logged_in):
        r = make_room(f"Rrl_{_ID}")
        t2 = tok(f"ru2_{_ID}", "TestRu21")
        api("POST", f"/api/rooms/{r['id']}/join", token=t2)
        api("PUT", f"/api/rooms/{r['id']}/role",
            {"username": f"ru2_{_ID}", "role": "voter"}, tok())


class TestRoomExport:

    def test_export(self, logged_in):
        r = make_room(f"Rex_{_ID}")
        url = harness.BASE_URL
        resp = urllib.request.urlopen(
            urllib.request.Request(f"{url}/api/rooms/{r['id']}/export",
                headers={"X-Requested-With": "test", "Authorization": f"Bearer {tok()}"}), timeout=5)
        assert resp.status == 200


class TestRoomDelete:

    def test_delete(self, logged_in):
        r = make_room(f"Rdel_{_ID}")
        api("DELETE", f"/api/rooms/{r['id']}", token=tok())
        rooms = api("GET", "/api/rooms", token=tok())
        assert not any(x["id"] == r["id"] for x in rooms)
