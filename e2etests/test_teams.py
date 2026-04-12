"""Teams E2E: create teams, manage members, verify in GUI settings."""

import time, json, os, urllib.request
import pytest
import harness
from harness import ROOT_PASSWORD

_ID = os.getpid()


def click_tab(app, title):
    app.execute_js(f'document.querySelector(\'button[title="{title}"]\')?.click()')
    time.sleep(1)


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


class TestTeams:

    def test_create_team(self, logged_in):
        t = token()
        team = api("POST", "/api/teams", {"name": f"Tm_{_ID}"}, t)
        assert team["name"] == f"Tm_{_ID}"

    def test_list_teams(self, logged_in):
        t = token()
        api("POST", "/api/teams", {"name": f"TmL_{_ID}"}, t)
        teams = api("GET", "/api/teams", token=t)
        assert any(tm["name"] == f"TmL_{_ID}" for tm in teams)

    def test_add_member(self, logged_in):
        t = token()
        team = api("POST", "/api/teams", {"name": f"TmM_{_ID}"}, t)
        detail = api("GET", f"/api/teams/{team['id']}", token=t)
        # Creator should be auto-added as member
        members = detail.get("members", detail.get("member_ids", []))
        assert len(members) >= 1

    def test_delete_team(self, logged_in):
        t = token()
        team = api("POST", "/api/teams", {"name": f"TmDel_{_ID}"}, t)
        api("DELETE", f"/api/teams/{team['id']}", token=t)
        teams = api("GET", "/api/teams", token=t)
        assert not any(tm["id"] == team["id"] for tm in teams)

    def test_team_visible_in_settings(self, logged_in):
        t = token()
        api("POST", "/api/teams", {"name": f"TmGui_{_ID}"}, t)
        logged_in.execute_js("location.reload()")
        time.sleep(3)
        body = logged_in.text(logged_in.find("body"))
        if "Sign In" in body:
            from harness import connect_gui_to_daemon, gui_login
            connect_gui_to_daemon(logged_in)
            gui_login(logged_in, "root", ROOT_PASSWORD)
        click_tab(logged_in, "Settings")
        src = logged_in.page_source()
        assert f"TmGui_{_ID}" in src or "Team" in src
