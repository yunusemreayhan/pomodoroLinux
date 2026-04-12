"""Tests for the helpers.py test library itself.

Ensures the test infrastructure is reliable — if helpers break,
every other test file becomes untrustworthy.
"""
import pytest
from helpers import H, _api, _api_status
import harness


class TestHInit:

    def test_root_default(self, logged_in):
        h = H()
        assert h.user == "root"
        assert h.password == harness.ROOT_PASSWORD

    def test_custom_user(self, logged_in):
        h = H("alice", "AlicePass1")
        assert h.user == "alice"
        assert h.password == "AlicePass1"

    def test_token_is_none_initially(self, logged_in):
        h = H()
        assert h._token is None


class TestHToken:

    def test_token_lazy_fetched(self, logged_in):
        h = H()
        assert h._token is None
        tok = h.token
        assert isinstance(tok, str)
        assert len(tok) > 20
        assert h._token is not None

    def test_token_cached(self, logged_in):
        h = H()
        t1 = h.token
        t2 = h.token
        assert t1 is t2  # Same object, not re-fetched

    def test_different_users_different_tokens(self, logged_in):
        root = H()
        alice = H.register("tok_alice")
        assert root.token != alice.token


class TestHRegister:

    def test_returns_h_instance(self, logged_in):
        u = H.register("reg_test1")
        assert isinstance(u, H)
        assert u.user == "reg_test1"

    def test_idempotent(self, logged_in):
        u1 = H.register("reg_idem")
        u2 = H.register("reg_idem")
        assert u1.user == u2.user

    def test_custom_password(self, logged_in):
        u = H.register("reg_pw", "CustomPw1")
        assert u.password == "CustomPw1"
        # Can actually authenticate
        assert len(u.token) > 20


class TestHApiStatus:

    def test_returns_tuple(self, logged_in):
        h = H()
        result = h.api_status("GET", "/api/health")
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_status_code_is_int(self, logged_in):
        h = H()
        code, _ = h.api_status("GET", "/api/health")
        assert isinstance(code, int)
        assert code == 200

    def test_error_returns_code(self, logged_in):
        h = H()
        code, _ = h.api_status("GET", "/api/tasks/999999")
        assert code in (404, 500)

    def test_unauthenticated_returns_401(self, logged_in):
        code, _ = _api_status("GET", "/api/tasks")
        assert code == 401


class TestHCreateTask:

    def test_returns_dict(self, logged_in):
        h = H()
        t = h.create_task("HelperTask")
        assert isinstance(t, dict)

    def test_has_id(self, logged_in):
        h = H()
        t = h.create_task("IdTask")
        assert "id" in t
        assert isinstance(t["id"], int)
        assert t["id"] > 0

    def test_has_title(self, logged_in):
        h = H()
        t = h.create_task("TitleTask")
        assert t["title"] == "TitleTask"

    def test_has_status(self, logged_in):
        h = H()
        t = h.create_task("StatusTask")
        assert "status" in t

    def test_default_project(self, logged_in):
        h = H()
        t = h.create_task("ProjTask")
        assert t.get("project") == "Test"

    def test_custom_fields(self, logged_in):
        h = H()
        t = h.create_task("Custom", project="MyProj", estimated=5, priority=3)
        assert t["project"] == "MyProj"
        assert t["estimated"] == 5
        assert t["priority"] == 3


class TestHCreateSprint:

    def test_returns_dict(self, logged_in):
        h = H()
        s = h.create_sprint("HelperSprint")
        assert isinstance(s, dict)

    def test_has_id_and_name(self, logged_in):
        h = H()
        s = h.create_sprint("NamedSprint")
        assert s["id"] > 0
        assert "NamedSprint" in s["name"]

    def test_has_status(self, logged_in):
        h = H()
        s = h.create_sprint("StatusSprint")
        assert s["status"] == "planning"


class TestHCreateRoom:

    def test_returns_dict(self, logged_in):
        h = H()
        r = h.create_room("HelperRoom")
        assert isinstance(r, dict)
        assert r["id"] > 0

    def test_has_name(self, logged_in):
        h = H()
        r = h.create_room("NamedRoom")
        assert "NamedRoom" in r["name"]


class TestHCreateLabel:

    def test_returns_dict(self, logged_in):
        h = H()
        lbl = h.create_label("HelperLabel")
        assert isinstance(lbl, dict)
        assert lbl["id"] > 0
        assert "HelperLabel" in lbl["name"]


class TestHCreateEpic:

    def test_returns_dict(self, logged_in):
        h = H()
        e = h.create_epic("HelperEpic")
        assert isinstance(e, dict)
        assert e["id"] > 0


class TestHCreateTeam:

    def test_returns_dict(self, logged_in):
        h = H()
        t = h.create_team("HelperTeam")
        assert isinstance(t, dict)
        assert t["id"] > 0


class TestHLogout:

    def test_clears_token(self, logged_in):
        import random
        u = H.register(f"logout_{random.randint(1000,9999)}")
        assert u._token is not None or u.token  # Force fetch
        u.logout()
        assert u._token is None


class TestHListMethods:

    def test_list_tasks_returns_list(self, logged_in):
        h = H()
        h.create_task("ListTest")
        tasks = h.list_tasks()
        assert isinstance(tasks, list)
        assert len(tasks) >= 1

    def test_list_sprints_returns_list(self, logged_in):
        h = H()
        sprints = h.list_sprints()
        assert isinstance(sprints, list)

    def test_list_labels_returns_list(self, logged_in):
        h = H()
        labels = h.list_labels()
        assert isinstance(labels, list)

    def test_list_rooms_returns_list(self, logged_in):
        h = H()
        rooms = h.list_rooms()
        assert isinstance(rooms, list)

    def test_history_returns_list(self, logged_in):
        h = H()
        hist = h.history()
        assert isinstance(hist, list)


class TestHComments:

    def test_add_comment_returns_dict(self, logged_in):
        h = H()
        t = h.create_task("CmTask")
        c = h.add_comment(t["id"], "Test comment")
        assert isinstance(c, dict)
        assert c["id"] > 0
        assert c["content"] == "Test comment"

    def test_list_comments_returns_list(self, logged_in):
        h = H()
        t = h.create_task("CmList")
        h.add_comment(t["id"], "One")
        comments = h.list_comments(t["id"])
        assert isinstance(comments, list)
        assert len(comments) >= 1


class TestHConfig:

    def test_get_config_returns_dict(self, logged_in):
        h = H()
        cfg = h.get_config()
        assert isinstance(cfg, dict)
        assert "work_duration_min" in cfg

    def test_update_config_returns_dict(self, logged_in):
        h = H()
        result = h.update_config(daily_goal=10)
        assert isinstance(result, dict)


class TestRawApi:

    def test_api_returns_parsed_json(self, logged_in):
        result = _api("GET", "/api/health")
        assert isinstance(result, dict)
        assert result.get("status") == "ok"

    def test_api_status_no_token(self, logged_in):
        code, body = _api_status("GET", "/api/health")
        assert code == 200
        assert isinstance(body, dict)
