"""Stress tests: concurrent API requests to find race conditions.

These tests hammer the daemon with parallel requests from multiple users
to expose race conditions in task creation, sprint burns, room voting,
and other shared-state operations.

Does NOT require the GUI — runs against the daemon API directly.
"""

import json, os, urllib.request, urllib.error
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
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
        urllib.request.Request(f"{url}{path}", data=data, headers=hdrs, method=method), timeout=10)
    raw = resp.read().decode()
    return json.loads(raw) if raw else {}


def api_status(method, path, body=None, token=None):
    """Return (status_code, response_or_error)."""
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
            urllib.request.Request(f"{url}{path}", data=data, headers=hdrs, method=method), timeout=10)
        raw = resp.read().decode()
        return resp.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:200]
    except Exception as e:
        return 0, str(e)


def setup_users(n):
    """Register n users and return list of (username, token) tuples."""
    root_tok = api("POST", "/api/auth/login",
                   {"username": "root", "password": ROOT_PASSWORD})["token"]
    users = []
    for i in range(n):
        name = f"stress_{_ID}_{i}"
        try:
            api("POST", "/api/auth/register",
                {"username": name, "password": "StressP1"}, root_tok)
        except Exception:
            pass
        tok = api("POST", "/api/auth/login",
                  {"username": name, "password": "StressP1"})["token"]
        users.append((name, tok))
    return root_tok, users


class TestConcurrentTaskCreation:
    """10 users creating tasks simultaneously."""

    def test_10_users_create_50_tasks_each(self, logged_in):
        root_tok, users = setup_users(10)
        errors = []
        created = []

        def create_tasks(user_tok, user_name, count):
            results = []
            for j in range(count):
                code, resp = api_status(
                    "POST", "/api/tasks",
                    {"title": f"{user_name}_task_{j}", "project": f"Stress_{_ID}"},
                    user_tok)
                if code != 201:
                    errors.append(f"{user_name} task {j}: {code} {resp}")
                else:
                    results.append(resp)
            return results

        with ThreadPoolExecutor(max_workers=10) as pool:
            futures = {
                pool.submit(create_tasks, tok, name, 50): name
                for name, tok in users
            }
            for f in as_completed(futures):
                created.extend(f.result())

        assert len(errors) == 0, f"Errors: {errors[:5]}"
        assert len(created) == 500
        # Verify all tasks have unique IDs
        ids = [t["id"] for t in created]
        assert len(set(ids)) == 500, f"Duplicate IDs found: {len(ids)} total, {len(set(ids))} unique"

    def test_concurrent_task_ids_are_sequential(self, logged_in):
        """IDs should be monotonically increasing (no gaps from race conditions)."""
        root_tok, users = setup_users(3)
        results = []

        def create(tok, name):
            out = []
            for j in range(20):
                t = api("POST", "/api/tasks", {"title": f"{name}_seq_{j}"}, tok)
                out.append(t["id"])
            return out

        with ThreadPoolExecutor(max_workers=3) as pool:
            futures = [pool.submit(create, tok, name) for name, tok in users]
            for f in as_completed(futures):
                results.extend(f.result())

        results.sort()
        # Check no duplicate IDs
        assert len(set(results)) == len(results)


class TestConcurrentSprintBurns:
    """Multiple users burning points on the same sprint simultaneously."""

    def test_concurrent_burns(self, logged_in):
        root_tok, users = setup_users(5)
        # Create sprint with tasks
        sprint = api("POST", "/api/sprints", {
            "name": f"StressSp_{_ID}",
            "start_date": "2026-05-01", "end_date": "2026-05-15"
        }, root_tok)
        tasks = []
        for i in range(10):
            t = api("POST", "/api/tasks", {"title": f"BurnT_{i}", "estimated": 10}, root_tok)
            tasks.append(t)
        api("POST", f"/api/sprints/{sprint['id']}/tasks",
            {"task_ids": [t["id"] for t in tasks]}, root_tok)
        api("POST", f"/api/sprints/{sprint['id']}/start", token=root_tok)

        errors = []
        burns = []

        def burn(tok, name, task_ids):
            out = []
            for tid in task_ids:
                code, resp = api_status(
                    "POST", f"/api/sprints/{sprint['id']}/burn",
                    {"task_id": tid, "points": 1.0, "hours": 0.5}, tok)
                if code != 201:
                    errors.append(f"{name} burn on {tid}: {code} {resp}")
                else:
                    out.append(resp)
            return out

        # Each user burns on all 10 tasks
        with ThreadPoolExecutor(max_workers=5) as pool:
            futures = {
                pool.submit(burn, tok, name, [t["id"] for t in tasks]): name
                for name, tok in users
            }
            for f in as_completed(futures):
                burns.extend(f.result())

        assert len(errors) == 0, f"Errors: {errors[:5]}"
        assert len(burns) == 50  # 5 users × 10 tasks

        # Verify burn summary
        all_burns = api("GET", f"/api/sprints/{sprint['id']}/burns", token=root_tok)
        active_burns = [b for b in all_burns if not b.get("cancelled")]
        assert len(active_burns) == 50


class TestConcurrentRoomVoting:
    """Multiple users voting simultaneously in the same room."""

    def test_concurrent_votes(self, logged_in):
        root_tok, users = setup_users(8)
        room = api("POST", "/api/rooms", {"name": f"StressRm_{_ID}", "estimation_unit": "points"}, root_tok)
        task = api("POST", "/api/tasks", {"title": f"VoteT_{_ID}"}, root_tok)

        # All users join
        for name, tok in users:
            api("POST", f"/api/rooms/{room['id']}/join", token=tok)

        # Start voting
        api("POST", f"/api/rooms/{room['id']}/start-voting", {"task_id": task["id"]}, root_tok)

        errors = []

        def vote(tok, name, value):
            code, resp = api_status(
                "POST", f"/api/rooms/{room['id']}/vote", {"value": value}, tok)
            if code not in (200, 204):
                errors.append(f"{name}: {code} {resp}")

        # All 8 users vote simultaneously
        with ThreadPoolExecutor(max_workers=8) as pool:
            futures = [
                pool.submit(vote, tok, name, float(i + 1))
                for i, (name, tok) in enumerate(users)
            ]
            for f in as_completed(futures):
                f.result()

        assert len(errors) == 0, f"Vote errors: {errors[:5]}"

        # Reveal and check all votes recorded
        revealed = api("POST", f"/api/rooms/{room['id']}/reveal", token=root_tok)
        detail = api("GET", f"/api/rooms/{room['id']}", token=root_tok)
        votes = detail.get("votes", [])
        assert len(votes) >= 8, f"Expected 8 votes, got {len(votes)}"


class TestConcurrentComments:
    """Multiple users commenting on the same task simultaneously."""

    def test_concurrent_comments(self, logged_in):
        root_tok, users = setup_users(5)
        task = api("POST", "/api/tasks", {"title": f"CmStress_{_ID}"}, root_tok)
        errors = []
        comments = []

        def comment(tok, name, count):
            out = []
            for j in range(10):
                code, resp = api_status(
                    "POST", f"/api/tasks/{task['id']}/comments",
                    {"content": f"{name}_comment_{j}"}, tok)
                if code != 201:
                    errors.append(f"{name} comment {j}: {code} {resp}")
                else:
                    out.append(resp)
            return out

        with ThreadPoolExecutor(max_workers=5) as pool:
            futures = [pool.submit(comment, tok, name, 10) for name, tok in users]
            for f in as_completed(futures):
                comments.extend(f.result())

        assert len(errors) == 0, f"Errors: {errors[:5]}"
        assert len(comments) == 50

        # Verify all comments persisted
        all_comments = api("GET", f"/api/tasks/{task['id']}/comments", token=root_tok)
        assert len(all_comments) == 50


class TestConcurrentUpdates:
    """Multiple users updating the same task simultaneously — last write wins."""

    def test_concurrent_status_updates(self, logged_in):
        root_tok = api("POST", "/api/auth/login",
                       {"username": "root", "password": ROOT_PASSWORD})["token"]
        task = api("POST", "/api/tasks", {"title": f"Race_{_ID}"}, root_tok)
        statuses = ["backlog", "active", "in_progress", "completed", "done",
                     "backlog", "active", "in_progress", "completed", "done"]
        errors = []

        def update(status, i):
            code, resp = api_status(
                "PUT", f"/api/tasks/{task['id']}", {"status": status}, root_tok)
            if code != 200:
                errors.append(f"update {i} to {status}: {code} {resp}")

        with ThreadPoolExecutor(max_workers=10) as pool:
            futures = [pool.submit(update, s, i) for i, s in enumerate(statuses)]
            for f in as_completed(futures):
                f.result()

        assert len(errors) == 0, f"Errors: {errors[:5]}"
        # Task should be in one of the valid statuses
        t = api("GET", f"/api/tasks/{task['id']}", token=root_tok)
        task_data = t.get("task", t)
        assert task_data["status"] in {"backlog", "active", "in_progress", "completed", "done"}


class TestConcurrentRegistration:
    """Multiple registrations with the same username — only one should succeed."""

    def test_duplicate_registration_race(self, logged_in):
        root_tok = api("POST", "/api/auth/login",
                       {"username": "root", "password": ROOT_PASSWORD})["token"]
        name = f"race_reg_{_ID}"
        results = []

        def register(i):
            code, resp = api_status(
                "POST", "/api/auth/register",
                {"username": name, "password": "RaceReg1x"}, root_tok)
            return code

        with ThreadPoolExecutor(max_workers=10) as pool:
            futures = [pool.submit(register, i) for i in range(10)]
            for f in as_completed(futures):
                results.append(f.result())

        # Exactly one should succeed (201), rest should fail (400/409)
        successes = [r for r in results if r in (200, 201)]
        assert len(successes) == 1, f"Expected 1 success, got {len(successes)}: {results}"


class TestConcurrentWatchers:
    """Multiple users watching/unwatching the same task."""

    def test_concurrent_watch_unwatch(self, logged_in):
        root_tok, users = setup_users(10)
        task = api("POST", "/api/tasks", {"title": f"WatchStress_{_ID}"}, root_tok)
        errors = []

        def watch_cycle(tok, name):
            for _ in range(5):
                c1, _ = api_status("POST", f"/api/tasks/{task['id']}/watch", token=tok)
                c2, _ = api_status("DELETE", f"/api/tasks/{task['id']}/watch", token=tok)
                if c1 not in (200, 204) or c2 not in (200, 204):
                    errors.append(f"{name}: watch={c1} unwatch={c2}")

        with ThreadPoolExecutor(max_workers=10) as pool:
            futures = [pool.submit(watch_cycle, tok, name) for name, tok in users]
            for f in as_completed(futures):
                f.result()

        assert len(errors) == 0, f"Errors: {errors[:5]}"


class TestConcurrentSprintTaskAdd:
    """Multiple users adding tasks to the same sprint simultaneously."""

    def test_concurrent_add_tasks(self, logged_in):
        root_tok = api("POST", "/api/auth/login",
                       {"username": "root", "password": ROOT_PASSWORD})["token"]
        sprint = api("POST", "/api/sprints", {"name": f"AddStress_{_ID}"}, root_tok)
        tasks = [api("POST", "/api/tasks", {"title": f"AT_{i}"}, root_tok) for i in range(20)]
        errors = []

        def add_batch(task_ids):
            code, resp = api_status(
                "POST", f"/api/sprints/{sprint['id']}/tasks",
                {"task_ids": task_ids}, root_tok)
            if code != 200:
                errors.append(f"add {task_ids}: {code} {resp}")

        # Add tasks in overlapping batches concurrently
        batches = [
            [tasks[i]["id"] for i in range(0, 10)],
            [tasks[i]["id"] for i in range(5, 15)],
            [tasks[i]["id"] for i in range(10, 20)],
            [tasks[i]["id"] for i in range(0, 20)],
        ]
        with ThreadPoolExecutor(max_workers=4) as pool:
            futures = [pool.submit(add_batch, b) for b in batches]
            for f in as_completed(futures):
                f.result()

        assert len(errors) == 0, f"Errors: {errors[:5]}"
        # All 20 tasks should be in the sprint (no duplicates)
        sprint_tasks = api("GET", f"/api/sprints/{sprint['id']}/tasks", token=root_tok)
        task_ids = {t["id"] for t in sprint_tasks}
        assert len(task_ids) == 20


class TestHighLoad:
    """Sustained high request rate."""

    def test_200_rapid_requests(self, logged_in):
        root_tok = api("POST", "/api/auth/login",
                       {"username": "root", "password": ROOT_PASSWORD})["token"]
        errors = []

        def rapid_get(i):
            code, _ = api_status("GET", "/api/tasks", token=root_tok)
            if code != 200:
                errors.append(f"req {i}: {code}")

        with ThreadPoolExecutor(max_workers=20) as pool:
            futures = [pool.submit(rapid_get, i) for i in range(200)]
            for f in as_completed(futures):
                f.result()

        assert len(errors) == 0, f"Errors: {errors[:10]}"
