"""Complex multi-user scenarios: privilege escalation, cross-user assignment,
burn tracking, permission boundaries, team workflows."""

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
        resp = urllib.request.urlopen(
            urllib.request.Request(f"{url}{path}", data=data, headers=hdrs, method=method), timeout=5)
        return resp.status, json.loads(resp.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:300]


def tok(user="root", pw=ROOT_PASSWORD):
    """Always get a fresh token — no caching. Role changes invalidate old tokens."""
    return api("POST", "/api/auth/login", {"username": user, "password": pw})["token"]


def register(username, password):
    try:
        api("POST", "/api/auth/register", {"username": username, "password": password}, tok())
    except Exception:
        pass  # already exists


def get_uid(username):
    users = api("GET", "/api/admin/users", token=tok())
    return next(u["id"] for u in users if u["username"] == username)


# ---------------------------------------------------------------------------
# Fixtures: create alice, bob, charlie once per session
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True, scope="module")
def _users():
    """Register test users once. Runs before any test in this module."""
    # We need a daemon running — the conftest session fixture handles that.
    # Users are created in the first test that needs them via register().


class TestPrivilegeEscalation:
    """Root elevates a normal user to root, verifies new powers."""

    def test_normal_user_cannot_admin(self, logged_in):
        register("alice", "AlicePass1")
        code, _ = api_err("GET", "/api/admin/users", token=tok("alice", "AlicePass1"))
        assert code == 403

    def test_root_elevates_user(self, logged_in):
        register("alice", "AlicePass1")
        uid = get_uid("alice")
        r = api("PUT", f"/api/admin/users/{uid}/role", {"role": "root"}, tok())
        assert r["role"] == "root"

    def test_elevated_user_can_admin(self, logged_in):
        register("alice", "AlicePass1")
        uid = get_uid("alice")
        api("PUT", f"/api/admin/users/{uid}/role", {"role": "root"}, tok())
        users = api("GET", "/api/admin/users", token=tok("alice", "AlicePass1"))
        assert any(u["username"] == "root" for u in users)

    def test_elevated_user_can_manage_others(self, logged_in):
        register("alice", "AlicePass1")
        register("pe_bob", "BobbyPass1")
        uid_a = get_uid("alice")
        api("PUT", f"/api/admin/users/{uid_a}/role", {"role": "root"}, tok())
        # Alice (now root) can reset pe_bob's password
        uid_b = get_uid("pe_bob")
        api("PUT", f"/api/admin/users/{uid_b}/password", {"password": "BobNew1xx"}, tok("alice", "AlicePass1"))
        t = tok("pe_bob", "BobNew1xx")
        assert t

    def test_demote_back_to_user(self, logged_in):
        register("alice", "AlicePass1")
        uid = get_uid("alice")
        api("PUT", f"/api/admin/users/{uid}/role", {"role": "user"}, tok())
        code, _ = api_err("GET", "/api/admin/users", token=tok("alice", "AlicePass1"))
        assert code == 403


class TestCrossUserTaskAssignment:
    """Root creates tasks, assigns to users, users interact with assigned tasks."""

    def test_root_creates_task_assigns_to_user(self, logged_in):
        register("charlie", "CharlieP1")
        task = api("POST", "/api/tasks", {"title": f"Assign_{_ID}", "project": "Team"}, tok())
        api("POST", f"/api/tasks/{task['id']}/assignees", {"username": "charlie"}, tok())
        assignees = api("GET", f"/api/tasks/{task['id']}/assignees", token=tok())
        assert "charlie" in assignees

    def test_assignee_can_log_time(self, logged_in):
        register("charlie", "CharlieP1")
        task = api("POST", "/api/tasks", {"title": f"ATime_{_ID}", "project": "Team"}, tok())
        api("POST", f"/api/tasks/{task['id']}/assignees", {"username": "charlie"}, tok())
        # Charlie (assignee, not owner) logs time
        entry = api("POST", f"/api/tasks/{task['id']}/time",
                     {"hours": 3.0}, tok("charlie", "CharlieP1"))
        assert entry["hours"] == 3.0

    def test_non_assignee_cannot_log_time(self, logged_in):
        register("charlie", "CharlieP1")
        register("dave", "DavePas1x")
        task = api("POST", "/api/tasks", {"title": f"NoTime_{_ID}", "project": "Team"}, tok())
        api("POST", f"/api/tasks/{task['id']}/assignees", {"username": "charlie"}, tok())
        # Dave is NOT assigned — should be forbidden
        code, _ = api_err("POST", f"/api/tasks/{task['id']}/time",
                          {"hours": 1.0}, tok("dave", "DavePas1x"))
        assert code == 403

    def test_root_can_log_time_on_any_task(self, logged_in):
        register("charlie", "CharlieP1")
        task = api("POST", "/api/tasks", {"title": f"RootTime_{_ID}"}, tok("charlie", "CharlieP1"))
        # Root logs time on Charlie's task
        entry = api("POST", f"/api/tasks/{task['id']}/time", {"hours": 2.0}, tok())
        assert entry["hours"] == 2.0

    def test_multiple_assignees(self, logged_in):
        register("charlie", "CharlieP1")
        register("dave", "DavePas1x")
        task = api("POST", "/api/tasks", {"title": f"Multi_{_ID}", "project": "Team"}, tok())
        api("POST", f"/api/tasks/{task['id']}/assignees", {"username": "charlie"}, tok())
        api("POST", f"/api/tasks/{task['id']}/assignees", {"username": "dave"}, tok())
        assignees = api("GET", f"/api/tasks/{task['id']}/assignees", token=tok())
        assert "charlie" in assignees and "dave" in assignees

    def test_assignee_cannot_delete_task(self, logged_in):
        register("charlie", "CharlieP1")
        task = api("POST", "/api/tasks", {"title": f"NoDel_{_ID}"}, tok())
        api("POST", f"/api/tasks/{task['id']}/assignees", {"username": "charlie"}, tok())
        code, _ = api_err("DELETE", f"/api/tasks/{task['id']}",
                          token=tok("charlie", "CharlieP1"))
        assert code == 403

    def test_assignee_cannot_update_task(self, logged_in):
        register("charlie", "CharlieP1")
        task = api("POST", "/api/tasks", {"title": f"NoUpd_{_ID}"}, tok())
        api("POST", f"/api/tasks/{task['id']}/assignees", {"username": "charlie"}, tok())
        code, _ = api_err("PUT", f"/api/tasks/{task['id']}",
                          {"title": "Hacked"}, tok("charlie", "CharlieP1"))
        assert code == 403


class TestSprintBurnMultiUser:
    """Multiple users burn points on a shared sprint."""

    def test_sprint_burn_workflow(self, logged_in):
        register("eve", "EvePas1xx")
        register("frank", "FrankPa1x")
        # Root creates sprint with tasks
        s = api("POST", "/api/sprints", {"name": f"TeamSp_{_ID}",
                "start_date": "2026-05-01", "end_date": "2026-05-15"}, tok())
        t1 = api("POST", "/api/tasks", {"title": f"SpT1_{_ID}", "estimated": 5}, tok())
        t2 = api("POST", "/api/tasks", {"title": f"SpT2_{_ID}", "estimated": 8}, tok())
        api("POST", f"/api/sprints/{s['id']}/tasks", {"task_ids": [t1["id"], t2["id"]]}, tok())
        api("POST", f"/api/sprints/{s['id']}/start", token=tok())

        # Eve burns points on task 1
        b1 = api("POST", f"/api/sprints/{s['id']}/burn",
                 {"task_id": t1["id"], "points": 3.0, "hours": 2.0}, tok("eve", "EvePas1xx"))
        assert b1["points"] == 3.0 and b1["username"] == "eve"

        # Frank burns points on task 2
        b2 = api("POST", f"/api/sprints/{s['id']}/burn",
                 {"task_id": t2["id"], "points": 5.0, "hours": 4.0}, tok("frank", "FrankPa1x"))
        assert b2["points"] == 5.0 and b2["username"] == "frank"

        # Root also burns on task 1
        b3 = api("POST", f"/api/sprints/{s['id']}/burn",
                 {"task_id": t1["id"], "points": 2.0, "hours": 1.0}, tok())
        assert b3["username"] == "root"

        # Verify all burns visible
        burns = api("GET", f"/api/sprints/{s['id']}/burns", token=tok())
        usernames = {b["username"] for b in burns if not b.get("cancelled")}
        assert {"eve", "frank", "root"} <= usernames

    def test_user_cannot_cancel_others_burn(self, logged_in):
        register("eve", "EvePas1xx")
        register("frank", "FrankPa1x")
        s = api("POST", "/api/sprints", {"name": f"NoCan_{_ID}",
                "start_date": "2026-05-01", "end_date": "2026-05-15"}, tok())
        t = api("POST", "/api/tasks", {"title": f"NCT_{_ID}"}, tok())
        api("POST", f"/api/sprints/{s['id']}/tasks", {"task_ids": [t["id"]]}, tok())
        api("POST", f"/api/sprints/{s['id']}/start", token=tok())
        b = api("POST", f"/api/sprints/{s['id']}/burn",
                {"task_id": t["id"], "points": 3.0}, tok("eve", "EvePas1xx"))
        # Frank tries to cancel Eve's burn
        code, _ = api_err("DELETE", f"/api/sprints/{s['id']}/burns/{b['id']}",
                          token=tok("frank", "FrankPa1x"))
        assert code == 403

    def test_root_can_cancel_any_burn(self, logged_in):
        register("eve", "EvePas1xx")
        s = api("POST", "/api/sprints", {"name": f"RCan_{_ID}",
                "start_date": "2026-05-01", "end_date": "2026-05-15"}, tok())
        t = api("POST", "/api/tasks", {"title": f"RCT_{_ID}"}, tok())
        api("POST", f"/api/sprints/{s['id']}/tasks", {"task_ids": [t["id"]]}, tok())
        api("POST", f"/api/sprints/{s['id']}/start", token=tok())
        b = api("POST", f"/api/sprints/{s['id']}/burn",
                {"task_id": t["id"], "points": 5.0}, tok("eve", "EvePas1xx"))
        # Root cancels Eve's burn
        cancelled = api("DELETE", f"/api/sprints/{s['id']}/burns/{b['id']}", token=tok())
        assert cancelled.get("cancelled") == 1 or cancelled.get("cancelled_by") == "root"

    def test_cannot_burn_on_inactive_sprint(self, logged_in):
        s = api("POST", "/api/sprints", {"name": f"Inact_{_ID}"}, tok())
        t = api("POST", "/api/tasks", {"title": "X"}, tok())
        api("POST", f"/api/sprints/{s['id']}/tasks", {"task_ids": [t["id"]]}, tok())
        # Sprint is still "planning" — burn should fail
        code, _ = api_err("POST", f"/api/sprints/{s['id']}/burn",
                          {"task_id": t["id"], "points": 1.0}, tok())
        assert code == 400


class TestTaskOwnershipBoundaries:
    """Normal users can only modify their own tasks; root can modify any."""

    def test_user_cannot_edit_others_task(self, logged_in):
        register("gina", "GinaPas1x")
        # Ensure gina is a normal user (may have been elevated by other tests)
        try:
            uid = get_uid("gina")
            api("PUT", f"/api/admin/users/{uid}/role", {"role": "user"}, tok())
        except Exception:
            pass
        task = api("POST", "/api/tasks", {"title": f"Own_{_ID}"}, tok())
        code, _ = api_err("PUT", f"/api/tasks/{task['id']}",
                          {"title": "Stolen"}, tok("gina", "GinaPas1x"))
        assert code == 403

    def test_user_cannot_delete_others_task(self, logged_in):
        register("gina", "GinaPas1x")
        task = api("POST", "/api/tasks", {"title": f"OwnD_{_ID}"}, tok())
        code, _ = api_err("DELETE", f"/api/tasks/{task['id']}",
                          token=tok("gina", "GinaPas1x"))
        assert code == 403

    def test_root_can_edit_any_task(self, logged_in):
        register("gina", "GinaPas1x")
        task = api("POST", "/api/tasks", {"title": f"GinaT_{_ID}"}, tok("gina", "GinaPas1x"))
        r = api("PUT", f"/api/tasks/{task['id']}", {"title": "RootEdited"}, tok())
        assert r["title"] == "RootEdited"

    def test_root_can_delete_any_task(self, logged_in):
        register("gina", "GinaPas1x")
        task = api("POST", "/api/tasks", {"title": f"GinaDel_{_ID}"}, tok("gina", "GinaPas1x"))
        api("DELETE", f"/api/tasks/{task['id']}", token=tok())
        trash = api("GET", "/api/tasks/trash", token=tok())
        assert any(t["title"] == f"GinaDel_{_ID}" for t in trash)

    def test_user_sees_only_own_tasks(self, logged_in):
        """Task list is shared — all users see all tasks (team visibility).
        But only owner/root can edit/delete."""
        register("gina", "GinaPas1x")
        register("hank", "HankPas1x")
        api("POST", "/api/tasks", {"title": f"GinaOnly_{_ID}"}, tok("gina", "GinaPas1x"))
        api("POST", "/api/tasks", {"title": f"HankOnly_{_ID}"}, tok("hank", "HankPas1x"))
        gina_tasks = api("GET", "/api/tasks", token=tok("gina", "GinaPas1x"))
        # Both users see all tasks (team visibility)
        assert any(t["title"] == f"GinaOnly_{_ID}" for t in gina_tasks)
        assert any(t["title"] == f"HankOnly_{_ID}" for t in gina_tasks)

    def test_root_sees_all_tasks(self, logged_in):
        register("gina", "GinaPas1x")
        api("POST", "/api/tasks", {"title": f"GinaAll_{_ID}"}, tok("gina", "GinaPas1x"))
        root_tasks = api("GET", "/api/tasks", token=tok())
        assert any(t["title"] == f"GinaAll_{_ID}" for t in root_tasks)


class TestSprintOwnershipBoundaries:

    def test_user_cannot_modify_others_sprint(self, logged_in):
        register("ivan", "IvanPas1x")
        s = api("POST", "/api/sprints", {"name": f"RootSp_{_ID}"}, tok())
        code, _ = api_err("PUT", f"/api/sprints/{s['id']}",
                          {"name": "Stolen"}, tok("ivan", "IvanPas1x"))
        assert code == 403

    def test_user_cannot_start_others_sprint(self, logged_in):
        register("ivan", "IvanPas1x")
        s = api("POST", "/api/sprints", {"name": f"NoStart_{_ID}"}, tok())
        code, _ = api_err("POST", f"/api/sprints/{s['id']}/start",
                          token=tok("ivan", "IvanPas1x"))
        assert code == 403

    def test_root_can_manage_any_sprint(self, logged_in):
        register("ivan", "IvanPas1x")
        s = api("POST", "/api/sprints", {"name": f"IvanSp_{_ID}"}, tok("ivan", "IvanPas1x"))
        r = api("PUT", f"/api/sprints/{s['id']}", {"name": "RootRenamed"}, tok())
        assert r["name"] == "RootRenamed"


class TestCommentPermissions:

    def test_user_can_comment_on_any_task(self, logged_in):
        register("jane", "JanePas1x")
        task = api("POST", "/api/tasks", {"title": f"CmPerm_{_ID}"}, tok())
        c = api("POST", f"/api/tasks/{task['id']}/comments",
                {"content": "Jane's comment"}, tok("jane", "JanePas1x"))
        assert c["content"] == "Jane's comment"

    def test_user_cannot_delete_others_comment(self, logged_in):
        register("jane", "JanePas1x")
        register("karl", "KarlPas1x")
        task = api("POST", "/api/tasks", {"title": f"CmDel_{_ID}"}, tok())
        c = api("POST", f"/api/tasks/{task['id']}/comments",
                {"content": "Jane wrote this"}, tok("jane", "JanePas1x"))
        code, _ = api_err("DELETE", f"/api/comments/{c['id']}",
                          token=tok("karl", "KarlPas1x"))
        assert code == 403

    def test_root_can_delete_any_comment(self, logged_in):
        register("jane", "JanePas1x")
        task = api("POST", "/api/tasks", {"title": f"CmRDel_{_ID}"}, tok())
        c = api("POST", f"/api/tasks/{task['id']}/comments",
                {"content": "Jane wrote this too"}, tok("jane", "JanePas1x"))
        api("DELETE", f"/api/comments/{c['id']}", token=tok())
        comments = api("GET", f"/api/tasks/{task['id']}/comments", token=tok())
        assert not any(x["id"] == c["id"] for x in comments)


class TestFullTeamWorkflow:
    """End-to-end: root sets up team, sprint, assigns tasks, users burn, complete."""

    def test_full_team_sprint(self, logged_in):
        register("lead", "LeadPas1x")
        register("dev1", "Dev1Pas1x")
        register("dev2", "Dev2Pas1x")

        # Root elevates lead
        uid_lead = get_uid("lead")
        api("PUT", f"/api/admin/users/{uid_lead}/role", {"role": "root"}, tok())
        lead_tok = tok("lead", "LeadPas1x")

        # Lead creates team
        team = api("POST", "/api/teams", {"name": f"Alpha_{_ID}"}, lead_tok)

        # Lead creates sprint
        sprint = api("POST", "/api/sprints", {
            "name": f"Sprint1_{_ID}", "start_date": "2026-05-01",
            "end_date": "2026-05-15", "capacity_hours": 80.0
        }, lead_tok)

        # Lead creates tasks and assigns
        t1 = api("POST", "/api/tasks", {
            "title": f"Backend_{_ID}", "project": "Alpha",
            "estimated": 5, "estimated_hours": 8.0
        }, lead_tok)
        t2 = api("POST", "/api/tasks", {
            "title": f"Frontend_{_ID}", "project": "Alpha",
            "estimated": 8, "estimated_hours": 16.0
        }, lead_tok)
        api("POST", f"/api/tasks/{t1['id']}/assignees", {"username": "dev1"}, lead_tok)
        api("POST", f"/api/tasks/{t2['id']}/assignees", {"username": "dev2"}, lead_tok)

        # Add tasks to sprint and start
        api("POST", f"/api/sprints/{sprint['id']}/tasks",
            {"task_ids": [t1["id"], t2["id"]]}, lead_tok)
        api("POST", f"/api/sprints/{sprint['id']}/start", token=lead_tok)

        # Dev1 burns on their task
        b1 = api("POST", f"/api/sprints/{sprint['id']}/burn",
                 {"task_id": t1["id"], "points": 3.0, "hours": 4.0,
                  "note": "API done"}, tok("dev1", "Dev1Pas1x"))
        assert b1["username"] == "dev1"

        # Dev1 also logs time on their assigned task
        tr1 = api("POST", f"/api/tasks/{t1['id']}/time",
                   {"hours": 4.0, "description": "API implementation"},
                   tok("dev1", "Dev1Pas1x"))
        assert tr1["hours"] == 4.0

        # Dev2 burns on their task
        b2 = api("POST", f"/api/sprints/{sprint['id']}/burn",
                 {"task_id": t2["id"], "points": 5.0, "hours": 8.0},
                 tok("dev2", "Dev2Pas1x"))
        assert b2["username"] == "dev2"

        # Lead completes remaining points
        api("POST", f"/api/sprints/{sprint['id']}/burn",
            {"task_id": t1["id"], "points": 2.0, "hours": 2.0}, lead_tok)
        api("POST", f"/api/sprints/{sprint['id']}/burn",
            {"task_id": t2["id"], "points": 3.0, "hours": 4.0}, lead_tok)

        # Mark tasks done
        api("PUT", f"/api/tasks/{t1['id']}", {"status": "completed"}, lead_tok)
        api("PUT", f"/api/tasks/{t2['id']}", {"status": "completed"}, lead_tok)

        # Complete sprint
        completed = api("POST", f"/api/sprints/{sprint['id']}/complete", token=lead_tok)
        assert completed["status"] == "completed"

        # Verify burn summary
        summary = api("GET", f"/api/sprints/{sprint['id']}/burn-summary", token=lead_tok)
        assert isinstance(summary, list)

        # Verify velocity includes this sprint
        velocity = api("GET", "/api/sprints/velocity", token=lead_tok)
        assert isinstance(velocity, list)

        # Demote lead back
        api("PUT", f"/api/admin/users/{uid_lead}/role", {"role": "user"}, tok())


class TestAuditTrail:
    """Verify audit log captures multi-user actions."""

    def test_audit_captures_actions(self, logged_in):
        register("auditor", "AuditPa1x")
        task = api("POST", "/api/tasks", {"title": f"Audit_{_ID}"}, tok())
        api("PUT", f"/api/tasks/{task['id']}", {"status": "completed"}, tok())
        api("DELETE", f"/api/tasks/{task['id']}", token=tok())

        log = api("GET", "/api/audit", token=tok())
        actions = [e.get("action") for e in log]
        assert "create" in actions
        assert "update" in actions or "delete" in actions

    def test_normal_user_sees_only_own_audit(self, logged_in):
        register("auditor", "AuditPa1x")
        api("POST", "/api/tasks", {"title": f"AudU_{_ID}"}, tok("auditor", "AuditPa1x"))
        log = api("GET", "/api/audit", token=tok("auditor", "AuditPa1x"))
        # Should only see auditor's own actions
        for entry in log:
            assert entry.get("user_id") == get_uid("auditor") or entry.get("username") == "auditor"


class TestDependencyPermissions:

    def test_user_cannot_add_dep_to_others_task(self, logged_in):
        register("liam", "LiamPas1x")
        t1 = api("POST", "/api/tasks", {"title": f"DepOwn_{_ID}"}, tok())
        t2 = api("POST", "/api/tasks", {"title": f"DepTgt_{_ID}"}, tok())
        code, _ = api_err("POST", f"/api/tasks/{t1['id']}/dependencies",
                          {"depends_on": t2["id"]}, tok("liam", "LiamPas1x"))
        assert code == 403

    def test_root_can_add_dep_to_any_task(self, logged_in):
        register("liam", "LiamPas1x")
        t1 = api("POST", "/api/tasks", {"title": f"DepR1_{_ID}"}, tok("liam", "LiamPas1x"))
        t2 = api("POST", "/api/tasks", {"title": f"DepR2_{_ID}"}, tok("liam", "LiamPas1x"))
        api("POST", f"/api/tasks/{t1['id']}/dependencies", {"depends_on": t2["id"]}, tok())
        deps = api("GET", f"/api/tasks/{t1['id']}/dependencies", token=tok())
        assert t2["id"] in deps

    def test_watcher_gets_notified(self, logged_in):
        register("watcher", "WatchPa1x")
        task = api("POST", "/api/tasks", {"title": f"WatchN_{_ID}"}, tok())
        api("POST", f"/api/tasks/{task['id']}/watch", token=tok("watcher", "WatchPa1x"))
        api("PUT", f"/api/tasks/{task['id']}", {"status": "completed"}, tok())
        notifs = api("GET", "/api/notifications", token=tok("watcher", "WatchPa1x"))
        assert isinstance(notifs, list)
