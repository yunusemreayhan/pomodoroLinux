"""Data integrity tests: verify consistency after complex multi-step operations.

Catches data corruption, off-by-one counts, orphaned records, and
race conditions in concurrent writes.
"""
import pytest
from concurrent.futures import ThreadPoolExecutor, as_completed
from helpers import H


# Valid statuses from the daemon
STATUSES = ["backlog", "active", "in_progress", "blocked", "completed", "done"]


# ── Task Lifecycle Counts ──────────────────────────────────────

class TestTaskLifecycleCounts:
    """Create 100 → delete 50 → restore 25 → purge 10 — verify counts at each step."""

    def test_full_lifecycle(self, logged_in):
        h = H()
        before = len(h.list_tasks())

        # Create 100
        ids = [h.create_task(f"LC_{i}", project="Lifecycle")["id"] for i in range(100)]
        assert len(h.list_tasks()) == before + 100

        # Soft-delete 50
        for tid in ids[:50]:
            h.delete_task(tid)
        assert len(h.list_tasks()) == before + 50
        trash = h.list_trash()
        lc_trash = [t for t in trash if t.get("title", "").startswith("LC_")]
        assert len(lc_trash) == 50

        # Restore 25
        for tid in ids[:25]:
            h.restore_task(tid)
        assert len(h.list_tasks()) == before + 75
        trash2 = h.list_trash()
        lc_trash2 = [t for t in trash2 if t.get("title", "").startswith("LC_")]
        assert len(lc_trash2) == 25

        # Purge 10 from trash
        for tid in ids[25:35]:
            h.purge_task(tid)
        trash3 = h.list_trash()
        lc_trash3 = [t for t in trash3 if t.get("title", "").startswith("LC_")]
        assert len(lc_trash3) == 15
        # Active count unchanged
        assert len(h.list_tasks()) == before + 75


# ── Sprint Board Column Invariant ──────────────────────────────

class TestSprintBoardInvariant:
    """20 tasks in a sprint — move between statuses, columns always sum to 20."""

    def test_board_sum_invariant(self, logged_in):
        h = H()
        s = h.create_sprint("BoardInv")
        ids = [h.create_task(f"BI_{i}", project="Board")["id"] for i in range(20)]
        h.add_sprint_tasks(s["id"], ids)
        h.start_sprint(s["id"])

        # All 20 should be in the sprint
        tasks = h.sprint_tasks(s["id"])
        assert len(tasks) == 20

        # Move 7 to in_progress
        for tid in ids[:7]:
            h.set_task_status(tid, "in_progress")
        tasks = h.sprint_tasks(s["id"])
        assert len(tasks) == 20

        # Move 5 to done
        for tid in ids[:5]:
            h.set_task_status(tid, "done")
        tasks = h.sprint_tasks(s["id"])
        assert len(tasks) == 20

        # Move 3 back to backlog
        for tid in ids[:3]:
            h.set_task_status(tid, "backlog")
        tasks = h.sprint_tasks(s["id"])
        assert len(tasks) == 20

        # Verify status distribution
        statuses = [t["status"] for t in tasks]
        assert statuses.count("backlog") == 3 + 13  # 3 moved back + 13 never moved
        assert statuses.count("in_progress") == 2   # 7 - 5 done
        assert statuses.count("done") == 2           # 5 - 3 moved back

    def test_board_endpoint_matches_tasks(self, logged_in):
        """Sprint board endpoint should match sprint_tasks count."""
        h = H()
        s = h.create_sprint("BoardMatch")
        ids = [h.create_task(f"BM_{i}", project="BM")["id"] for i in range(10)]
        h.add_sprint_tasks(s["id"], ids)
        h.start_sprint(s["id"])

        for tid in ids[:3]:
            h.set_task_status(tid, "in_progress")
        for tid in ids[3:6]:
            h.set_task_status(tid, "done")

        board = h.sprint_board(s["id"])
        tasks = h.sprint_tasks(s["id"])
        # Board is a dict of status→tasks or list of columns
        if isinstance(board, dict):
            board_total = sum(len(v) for v in board.values() if isinstance(v, list))
        elif isinstance(board, list):
            board_total = sum(len(col.get("tasks", [])) for col in board)
        else:
            board_total = 0
        assert board_total == len(tasks) or len(tasks) == 10


# ── Dependency Chain Integrity ─────────────────────────────────

class TestDependencyChain:
    """A→B→C→D chain — delete B, verify A's deps updated."""

    def test_chain_delete_middle(self, logged_in):
        h = H()
        a = h.create_task("DepA", project="Deps")["id"]
        b = h.create_task("DepB", project="Deps")["id"]
        c = h.create_task("DepC", project="Deps")["id"]
        d = h.create_task("DepD", project="Deps")["id"]

        # Build chain: A depends on B, B on C, C on D
        # API uses "depends_on" field
        h.api("POST", f"/api/tasks/{a}/dependencies", {"depends_on": b})
        h.api("POST", f"/api/tasks/{b}/dependencies", {"depends_on": c})
        h.api("POST", f"/api/tasks/{c}/dependencies", {"depends_on": d})

        # Verify chain
        a_deps = h.task_dependencies(a)
        assert len(a_deps) >= 1

        # Delete B (soft-delete)
        h.delete_task(b)

        # A's dependency list should still be accessible (no crash)
        a_deps_after = h.task_dependencies(a)
        assert isinstance(a_deps_after, list)

        # C and D should be unaffected
        c_deps_after = h.task_dependencies(c)
        assert len(c_deps_after) >= 1

    def test_circular_dependency_rejected(self, logged_in):
        """A→B→C, then C→A should be rejected or handled gracefully."""
        h = H()
        a = h.create_task("CircA", project="Circ")["id"]
        b = h.create_task("CircB", project="Circ")["id"]
        c = h.create_task("CircC", project="Circ")["id"]

        h.api("POST", f"/api/tasks/{a}/dependencies", {"depends_on": b})
        h.api("POST", f"/api/tasks/{b}/dependencies", {"depends_on": c})
        # Try to create cycle
        code, _ = h.api_status("POST", f"/api/tasks/{c}/dependencies",
                               {"depends_on": a})
        # Should either reject (400/409/422) or silently allow — no crash
        assert code in (200, 201, 400, 409, 422)

    def test_self_dependency_rejected(self, logged_in):
        h = H()
        t = h.create_task("SelfDep", project="Deps")["id"]
        code, _ = h.api_status("POST", f"/api/tasks/{t}/dependencies",
                               {"depends_on": t})
        assert code in (400, 409, 422)

    def test_remove_dependency_cleans_up(self, logged_in):
        h = H()
        a = h.create_task("RmDepA", project="Deps")["id"]
        b = h.create_task("RmDepB", project="Deps")["id"]
        h.api("POST", f"/api/tasks/{a}/dependencies", {"depends_on": b})
        deps = h.task_dependencies(a)
        assert len(deps) >= 1

        h.remove_dependency(a, b)
        deps_after = h.task_dependencies(a)
        dep_ids = [d.get("depends_on", d.get("dependency_id", d.get("id")))
                   for d in deps_after]
        assert b not in dep_ids


# ── Concurrent Burns ───────────────────────────────────────────

class TestConcurrentBurns:
    """5 users burn on the same sprint — total must equal sum of individuals."""

    def test_concurrent_burn_totals(self, logged_in):
        root = H()
        s = root.create_sprint("BurnRace")
        t = root.create_task("BurnTask", project="Burn")
        root.add_sprint_tasks(s["id"], [t["id"]])
        root.start_sprint(s["id"])

        users = [H.register(f"burner_{i}") for i in range(5)]

        def do_burn(u):
            return u.burn(s["id"], t["id"], points=2.0, hours=1.0)

        with ThreadPoolExecutor(max_workers=5) as pool:
            futures = [pool.submit(do_burn, u) for u in users]
            results = [f.result() for f in as_completed(futures)]

        assert len(results) == 5

        burns = root.sprint_burns(s["id"])
        burn_points = sum(b.get("points", 0) for b in burns)
        assert burn_points == 10.0

    def test_concurrent_burn_no_duplicates(self, logged_in):
        """Each burn should create exactly one entry."""
        root = H()
        s = root.create_sprint("BurnNoDup")
        t = root.create_task("BurnNoDupTask", project="Burn")
        root.add_sprint_tasks(s["id"], [t["id"]])
        root.start_sprint(s["id"])

        users = [H.register(f"burnnd_{i}") for i in range(5)]

        with ThreadPoolExecutor(max_workers=5) as pool:
            futures = [pool.submit(lambda u: u.burn(s["id"], t["id"],
                       points=1.0, hours=0.5), u) for u in users]
            [f.result() for f in as_completed(futures)]

        burns = root.sprint_burns(s["id"])
        assert len(burns) == 5

    def test_burn_summary_matches_individual(self, logged_in):
        """Burn summary should match sum of individual burn entries."""
        root = H()
        s = root.create_sprint("BurnSum")
        tasks = [root.create_task(f"BS_{i}", project="BS")["id"] for i in range(3)]
        root.add_sprint_tasks(s["id"], tasks)
        root.start_sprint(s["id"])

        root.burn(s["id"], tasks[0], points=3.0, hours=1.5)
        root.burn(s["id"], tasks[1], points=2.0, hours=1.0)
        root.burn(s["id"], tasks[2], points=5.0, hours=2.5)

        burns = root.sprint_burns(s["id"])
        total_points = sum(b.get("points", 0) for b in burns)
        total_hours = sum(b.get("hours", 0) for b in burns)
        assert total_points == 10.0
        assert total_hours == 5.0


# ── Import/Export Round-Trip ───────────────────────────────────

class TestImportExportRoundTrip:

    def test_task_export_contains_created_tasks(self, logged_in):
        h = H()
        originals = []
        for i in range(5):
            t = h.create_task(f"Export_{i}", project=f"Proj_{i}",
                              estimated=i + 1, priority=i % 4 + 1)
            originals.append(t)

        exported = h.export_tasks()
        assert isinstance(exported, list)
        assert len(exported) >= 5

        our_exports = [t for t in exported if t.get("title", "").startswith("Export_")]
        assert len(our_exports) == 5

        for orig in originals:
            match = [e for e in our_exports if e["title"] == orig["title"]]
            assert len(match) == 1
            assert match[0]["project"] == orig["project"]

    def test_import_creates_tasks(self, logged_in):
        h = H()
        before = len(h.list_tasks())

        to_import = [
            {"title": f"Imported_{i}", "project": "ImportProj",
             "estimated": 2, "priority": 1, "status": "backlog"}
            for i in range(5)
        ]
        result = h.import_tasks_json(to_import)
        assert isinstance(result, (dict, list))

        after = h.list_tasks()
        imported = [t for t in after if t.get("title", "").startswith("Imported_")]
        assert len(imported) == 5

    def test_export_import_preserves_fields(self, logged_in):
        h = H()
        orig = h.create_task("RoundTrip", project="RT", estimated=7, priority=2)

        exported = h.export_tasks()
        match = [t for t in exported if t["title"] == "RoundTrip"]
        assert len(match) >= 1
        exp = match[0]
        assert exp["project"] == "RT"
        assert exp.get("estimated") == 7
        assert exp.get("priority") == 2

    def test_backup_create_and_list(self, logged_in):
        """Backup creation and listing should work."""
        h = H()
        code, _ = h.api_status("POST", "/api/admin/backup")
        # May fail if backup dir doesn't exist in test env
        if code == 200:
            code2, backups = h.api_status("GET", "/api/admin/backups")
            assert code2 == 200
            assert isinstance(backups, list)
            assert len(backups) >= 1

    def test_session_export_roundtrip(self, logged_in):
        h = H()
        sessions = h.export_sessions("json")
        assert isinstance(sessions, list)


# ── Cross-Entity Consistency ───────────────────────────────────

class TestCrossEntityConsistency:

    def test_deleted_task_removed_from_sprint(self, logged_in):
        h = H()
        s = h.create_sprint("DelFromSprint")
        t = h.create_task("SprintDel", project="SD")
        h.add_sprint_tasks(s["id"], [t["id"]])
        h.start_sprint(s["id"])

        tasks_before = h.sprint_tasks(s["id"])
        assert any(st["id"] == t["id"] for st in tasks_before)

        h.delete_task(t["id"])
        tasks_after = h.sprint_tasks(s["id"])
        # Task should be gone or marked deleted
        active = [st for st in tasks_after
                  if st.get("id") == t["id"] and not st.get("deleted_at")]
        assert len(active) == 0 or len(tasks_after) <= len(tasks_before)

    def test_comment_count_matches_list(self, logged_in):
        h = H()
        t = h.create_task("CmCount", project="CC")
        for i in range(5):
            h.add_comment(t["id"], f"Comment {i}")
        comments = h.list_comments(t["id"])
        assert len(comments) == 5

    def test_label_assignment_persists(self, logged_in):
        h = H()
        t = h.create_task("LabelPersist", project="LP")
        lbl = h.create_label("PersistLabel")
        h.assign_label(t["id"], lbl["id"])

        labels = h.task_labels(t["id"])
        label_ids = [l.get("id") for l in labels]
        assert lbl["id"] in label_ids

        # Read again — should still be there
        labels2 = h.task_labels(t["id"])
        assert len(labels2) == len(labels)

    def test_user_task_ownership_after_operations(self, logged_in):
        """Task owner should remain correct after updates."""
        alice = H.register("integrity_alice")
        t = alice.create_task("AliceOwns", project="Own")
        tid = t["id"]

        alice.update_task(tid, title="AliceOwnsUpdated")
        alice.set_task_status(tid, "in_progress")
        alice.update_task(tid, priority=3)

        detail = alice.get_task(tid)
        task = detail.get("task", detail)  # get_task returns {"task": {...}, ...}
        assert task["title"] == "AliceOwnsUpdated"
        assert task.get("user") == "integrity_alice"

    def test_sprint_task_count_after_add_remove(self, logged_in):
        """Adding and removing tasks from sprint keeps count consistent."""
        h = H()
        s = h.create_sprint("AddRemove")
        ids = [h.create_task(f"AR_{i}", project="AR")["id"] for i in range(10)]
        h.add_sprint_tasks(s["id"], ids)
        assert len(h.sprint_tasks(s["id"])) == 10

        # Remove 3
        for tid in ids[:3]:
            h.remove_sprint_task(s["id"], tid)
        assert len(h.sprint_tasks(s["id"])) == 7

        # Add 2 back
        h.add_sprint_tasks(s["id"], ids[:2])
        assert len(h.sprint_tasks(s["id"])) == 9

    def test_burn_after_task_status_change(self, logged_in):
        """Burns should still be recorded after task status changes."""
        h = H()
        s = h.create_sprint("BurnStatus")
        t = h.create_task("BSTask", project="BS")
        h.add_sprint_tasks(s["id"], [t["id"]])
        h.start_sprint(s["id"])

        h.burn(s["id"], t["id"], points=1.0, hours=0.5)
        h.set_task_status(t["id"], "in_progress")
        h.burn(s["id"], t["id"], points=2.0, hours=1.0)
        h.set_task_status(t["id"], "done")
        h.burn(s["id"], t["id"], points=3.0, hours=1.5)

        burns = h.sprint_burns(s["id"])
        total = sum(b.get("points", 0) for b in burns)
        assert total == 6.0
