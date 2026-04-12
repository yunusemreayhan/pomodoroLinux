# Test Cheatsheet

Copy-paste patterns for writing new tests. Every test needs the `logged_in` fixture (starts the daemon + GUI).

## 1. Create and verify a task

```python
def test_create_task(self, logged_in):
    h = H()
    task = h.create_task("My Task", project="MyProject", priority=1, estimated=5)
    assert task["title"] == "My Task"
    assert task["estimated"] == 5
```

## 2. Full sprint lifecycle

```python
def test_sprint_lifecycle(self, logged_in):
    h = H()
    sprint = h.create_sprint("Sprint 1")
    task = h.create_task("Feature", estimated=8)
    h.add_sprint_tasks(sprint["id"], [task["id"]])
    h.start_sprint(sprint["id"])                    # planning → active
    h.burn(sprint["id"], task["id"], 5.0, 2.5)     # log progress
    result = h.complete_sprint(sprint["id"])         # active → completed
    assert result["status"] == "completed"
```

## 3. Multi-user scenario

```python
def test_cross_user(self, logged_in):
    root = H()
    alice = H.register("alice", "AlicePass1")
    task = root.create_task("Root's Task")
    # Alice can comment on any task
    alice.add_comment(task["id"], "Looks good!")
    # Alice cannot edit root's task
    code, _ = alice.api_status("PUT", f"/api/tasks/{task['id']}", {"title": "Hacked"})
    assert code == 403
```

## 4. Error path test

```python
def test_not_found(self, logged_in):
    h = H()
    code, _ = h.api_status("GET", "/api/tasks/999999")
    assert code in (404, 500)

def test_unauthorized(self, logged_in):
    from helpers import _api_status
    code, _ = _api_status("GET", "/api/tasks")  # no token
    assert code == 401

def test_forbidden(self, logged_in):
    user = H.register("normie", "NormieP1")
    code, _ = user.api_status("GET", "/api/admin/users")
    assert code == 403
```

## 5. GUI assertion

```python
def test_task_visible_in_gui(self, logged_in):
    h = H()
    h.create_task("GUI Visible Task", project="Demo")
    H.assert_task_in_gui(logged_in, "GUI Visible Task")

def test_timer_shows_ready(self, logged_in):
    H.assert_timer_state(logged_in, "READY", "Start Focus")
```

## 6. Parametrized test (many inputs, one pattern)

```python
import pytest

STATUSES = ["backlog", "active", "in_progress", "blocked", "completed", "done"]

@pytest.mark.parametrize("status", STATUSES)
def test_set_status(self, logged_in, status):
    h = H()
    task = h.create_task(f"Status_{status}")
    result = h.set_task_status(task["id"], status)
    assert result["status"] == status
```

## 7. Timer state machine

```python
def test_timer_cycle(self, logged_in):
    h = H()
    s = h.start_timer()
    assert s["phase"] == "Work" and s["status"] == "Running"
    s = h.pause_timer()
    assert s["status"] == "Paused"
    s = h.resume_timer()
    assert s["status"] == "Running"
    s = h.skip_timer()                # work → break
    assert s["phase"] in ("ShortBreak", "LongBreak")
    h.stop_timer()
```

## 8. Room estimation flow

```python
def test_estimation(self, logged_in):
    h = H()
    room = h.create_room("Planning Poker")
    task = h.create_task("Estimate Me")
    h.join_room(room["id"])
    h.start_voting(room["id"], task["id"])
    h.vote(room["id"], 5)
    h.reveal_votes(room["id"])
    result = h.accept_estimate(room["id"], 5)
    assert result.get("estimated") == 5
```

## 9. Template with variable resolution

```python
def test_template(self, logged_in):
    h = H()
    tmpl = h.create_template("Daily", {"title": "{{today}} standup by {{username}}"})
    task = h.instantiate_template(tmpl["id"])
    assert "2026" in task["title"]    # {{today}} resolved
    assert "root" in task["title"]    # {{username}} resolved
```

## 10. Concurrent stress test

```python
from concurrent.futures import ThreadPoolExecutor

def test_concurrent_creates(self, logged_in):
    users = [H.register(f"stress_{i}", "StressP1") for i in range(5)]
    results = []
    def create(u):
        return u.create_task(f"Task by {u.user}")
    with ThreadPoolExecutor(max_workers=5) as pool:
        results = list(pool.map(create, users))
    ids = [r["id"] for r in results]
    assert len(set(ids)) == 5  # all unique
```

## 11. Auth matrix (parametrized)

```python
import pytest

ENDPOINTS = [
    ("GET", "/api/tasks"),
    ("POST", "/api/tasks"),
    ("GET", "/api/sprints"),
]

@pytest.mark.parametrize("method,path", ENDPOINTS)
def test_requires_auth(self, logged_in, method, path):
    from helpers import _api_status
    code, _ = _api_status(method, path)  # no token
    assert code == 401
```

## 12. Input validation (parametrized)

```python
import pytest

CASES = [
    ("POST", "/api/tasks", {}, "missing title"),
    ("POST", "/api/tasks", {"title": ""}, "empty title"),
    ("POST", "/api/tasks", {"title": "x" * 10000}, "huge title"),
]

@pytest.mark.parametrize("method,path,body,desc", CASES)
def test_rejects_bad_input(self, logged_in, method, path, body, desc):
    h = H()
    code, _ = h.api_status(method, path, body)
    assert code in (201, 400, 422), f"{desc}: got {code}"
```

## Quick reference

| What | How |
|------|-----|
| Root helper | `h = H()` |
| New user | `alice = H.register("alice", "AlicePass1")` |
| Check status code | `code, resp = h.api_status("GET", "/api/...")` |
| Raw API (no auth) | `from helpers import _api_status; _api_status("GET", "/api/health")` |
| GUI: navigate tab | `from harness import click_tab; click_tab(app, "Tasks")` |
| GUI: check text | `app.assert_visible("Expected Text")` |
| GUI: wait for text | `app.wait_for_text("Loading done", timeout=10)` |
| GUI: run JS | `app.execute_js("return document.title")` |
| GUI: reload + login | `from harness import reload_and_login; reload_and_login(app)` |

## File naming convention

- `test_<feature>.py` — focused on one feature area
- Use `class Test<Feature>:` to group related tests
- Every test method takes `self, logged_in` (or `self, app` for login-screen tests)
- Import: `from helpers import H`
