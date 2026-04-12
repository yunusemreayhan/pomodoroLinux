"""Sprint transitions: planning → active → completed, carryover, and edge cases."""
import pytest
from helpers import H


class TestSprintTransitions:

    def test_planning_to_active(self, logged_in):
        h = H()
        s = h.create_sprint("PlanActive")
        t = h.create_task("ST1")
        h.add_sprint_tasks(s["id"], [t["id"]])
        r = h.start_sprint(s["id"])
        assert r["status"] == "active"

    def test_active_to_completed(self, logged_in):
        h = H()
        s = h.create_sprint("ActiveComp")
        t = h.create_task("ST2")
        h.add_sprint_tasks(s["id"], [t["id"]])
        h.start_sprint(s["id"])
        r = h.complete_sprint(s["id"])
        assert r["status"] == "completed"

    def test_cannot_start_completed_sprint(self, logged_in):
        h = H()
        s = h.create_sprint("CompStart")
        t = h.create_task("ST3")
        h.add_sprint_tasks(s["id"], [t["id"]])
        h.start_sprint(s["id"])
        h.complete_sprint(s["id"])
        code, _ = h.api_status("POST", f"/api/sprints/{s['id']}/start")
        assert code >= 400

    def test_cannot_complete_planning_sprint(self, logged_in):
        h = H()
        s = h.create_sprint("PlanComp")
        code, _ = h.api_status("POST", f"/api/sprints/{s['id']}/complete")
        assert code >= 400

    def test_carryover_creates_new_sprint(self, logged_in):
        h = H()
        s = h.create_sprint("Carry1")
        t = h.create_task("CarryT", status="backlog")
        h.add_sprint_tasks(s["id"], [t["id"]])
        h.start_sprint(s["id"])
        h.complete_sprint(s["id"])
        new = h.sprint_carryover(s["id"])
        assert new["id"] != s["id"]
        assert new["status"] == "planning"


class TestSprintBurns:

    def test_burn_on_active_sprint(self, logged_in):
        h = H()
        s = h.create_sprint("BurnAct")
        t = h.create_task("BT1", estimated=10)
        h.add_sprint_tasks(s["id"], [t["id"]])
        h.start_sprint(s["id"])
        b = h.burn(s["id"], t["id"], 3.0, 1.5)
        assert b["points"] == 3.0

    def test_burn_on_planning_sprint_fails(self, logged_in):
        h = H()
        s = h.create_sprint("BurnPlan")
        t = h.create_task("BT2")
        h.add_sprint_tasks(s["id"], [t["id"]])
        code, _ = h.api_status("POST", f"/api/sprints/{s['id']}/burn",
                               {"task_id": t["id"], "points": 1, "hours": 0.5})
        assert code >= 400

    def test_cancel_burn(self, logged_in):
        h = H()
        s = h.create_sprint("BurnCancel")
        t = h.create_task("BT3", estimated=5)
        h.add_sprint_tasks(s["id"], [t["id"]])
        h.start_sprint(s["id"])
        b = h.burn(s["id"], t["id"])
        r = h.cancel_burn(s["id"], b["id"])
        assert r.get("cancelled") or r.get("canceled")

    def test_burn_summary(self, logged_in):
        h = H()
        s = h.create_sprint("BurnSum")
        t = h.create_task("BT4", estimated=5)
        h.add_sprint_tasks(s["id"], [t["id"]])
        h.start_sprint(s["id"])
        h.burn(s["id"], t["id"], 2.0, 1.0)
        summary = h.sprint_burn_summary(s["id"])
        assert isinstance(summary, list)


class TestSprintBoard:

    def test_board_columns(self, logged_in):
        h = H()
        s = h.create_sprint("Board1")
        t1 = h.create_task("BdT1", status="backlog")
        t2 = h.create_task("BdT2", status="in_progress")
        h.add_sprint_tasks(s["id"], [t1["id"], t2["id"]])
        h.start_sprint(s["id"])
        board = h.sprint_board(s["id"])
        assert isinstance(board, dict)

    def test_snapshot(self, logged_in):
        h = H()
        s = h.create_sprint("Snap1")
        t = h.create_task("SnapT")
        h.add_sprint_tasks(s["id"], [t["id"]])
        h.start_sprint(s["id"])
        snap = h.sprint_snapshot(s["id"])
        assert isinstance(snap, dict)


class TestSprintScope:

    def test_scope_returns_list(self, logged_in):
        h = H()
        s = h.create_sprint("Scope1")
        t1 = h.create_task("ScT1")
        h.add_sprint_tasks(s["id"], [t1["id"]])
        scope = h.sprint_scope(s["id"])
        assert isinstance(scope, list)

    def test_remove_task_from_sprint(self, logged_in):
        h = H()
        s = h.create_sprint("RmTask")
        t = h.create_task("RmT")
        h.add_sprint_tasks(s["id"], [t["id"]])
        h.remove_sprint_task(s["id"], t["id"])
        tasks = h.sprint_tasks(s["id"])
        assert not any(x["id"] == t["id"] for x in tasks)


class TestSprintRoots:

    def test_add_remove_root(self, logged_in):
        h = H()
        s = h.create_sprint("Root1")
        t = h.create_task("RootT")
        h.add_sprint_tasks(s["id"], [t["id"]])
        h.add_sprint_root(s["id"], t["id"])
        roots = h.sprint_roots(s["id"])
        assert t["id"] in roots
        h.remove_sprint_root(s["id"], t["id"])
        roots = h.sprint_roots(s["id"])
        assert t["id"] not in roots


class TestSprintCompare:

    def test_compare_two_sprints(self, logged_in):
        h = H()
        s1 = h.create_sprint("Cmp1")
        s2 = h.create_sprint("Cmp2")
        r = h.sprint_compare(s1["id"], s2["id"])
        assert isinstance(r, dict)


class TestSprintErrors:

    def test_start_nonexistent_sprint(self, logged_in):
        h = H()
        code, _ = h.api_status("POST", "/api/sprints/999999/start")
        assert code == 404

    def test_delete_active_sprint(self, logged_in):
        h = H()
        s = h.create_sprint("DelAct")
        t = h.create_task("DAT")
        h.add_sprint_tasks(s["id"], [t["id"]])
        h.start_sprint(s["id"])
        code, _ = h.delete_sprint(s["id"])
        # May succeed or fail depending on policy
        assert code in (204, 400, 409)
