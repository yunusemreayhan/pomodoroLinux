"""Task status transitions: every valid and invalid transition between all 8 statuses."""
import pytest
from helpers import H

STATUSES = ["backlog", "active", "in_progress", "blocked", "completed", "done", "estimated", "archived"]


class TestStatusTransitions:
    """Every status can be set directly — no state machine restrictions."""

    @pytest.mark.parametrize("from_s,to_s", [
        (a, b) for a in STATUSES for b in STATUSES if a != b
    ])
    def test_transition(self, logged_in, from_s, to_s):
        h = H()
        t = h.create_task(f"Trans_{from_s}_{to_s}")
        h.set_task_status(t["id"], from_s)
        r = h.set_task_status(t["id"], to_s)
        assert r["status"] == to_s


class TestStatusBulk:
    """Bulk status update for multiple tasks."""

    @pytest.mark.parametrize("status", STATUSES)
    def test_bulk_to_status(self, logged_in, status):
        h = H()
        ids = [h.create_task(f"Bulk_{status}_{i}")["id"] for i in range(3)]
        h.bulk_status(ids, status)
        for tid in ids:
            t = h.get_task(tid)
            task = t.get("task", t)
            assert task["status"] == status


class TestStatusInvalid:

    def test_invalid_status_rejected(self, logged_in):
        h = H()
        t = h.create_task("BadStatus")
        code, _ = h.api_status("PUT", f"/api/tasks/{t['id']}", {"status": "nonexistent"})
        assert code == 400

    def test_empty_status_rejected(self, logged_in):
        h = H()
        t = h.create_task("EmptyStatus")
        code, _ = h.api_status("PUT", f"/api/tasks/{t['id']}", {"status": ""})
        assert code == 400
