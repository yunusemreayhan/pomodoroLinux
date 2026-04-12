"""High-level test helpers for pomodoroLinux E2E tests.

Import these to write tests in 3-5 lines instead of raw API calls.
Every helper handles auth, returns the created object, and is composable.

Usage:
    from helpers import H
    h = H()                          # uses root token
    task = h.create_task("My Task")
    h.add_comment(task["id"], "hello")
    h.assert_task_exists(task["id"])
"""

import json, os, urllib.request, urllib.error
import harness
from harness import ROOT_PASSWORD

_ID = os.getpid()


def _api(method, path, body=None, token=None):
    """Raw API call — returns parsed JSON."""
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


def _api_status(method, path, body=None, token=None):
    """Raw API call — returns (status_code, response_or_error)."""
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
        return e.code, e.read().decode()[:500]


class H:
    """High-level test helper. One instance per user."""

    def __init__(self, user="root", password=ROOT_PASSWORD):
        self.user = user
        self.password = password
        self._token = None

    @property
    def token(self):
        if not self._token:
            self._token = _api("POST", "/api/auth/login",
                               {"username": self.user, "password": self.password})["token"]
        return self._token

    def api(self, method, path, body=None):
        return _api(method, path, body, self.token)

    def api_status(self, method, path, body=None):
        return _api_status(method, path, body, self.token)

    # ── Auth ────────────────────────────────────────────────────

    @staticmethod
    def register(username, password="TestPass1"):
        """Register a new user, return H instance. Idempotent."""
        try:
            _api("POST", "/api/auth/register", {"username": username, "password": password})
        except Exception:
            pass
        return H(username, password)

    def logout(self):
        self.api("POST", "/api/auth/logout")
        self._token = None

    def refresh(self):
        r = self.api("POST", "/api/auth/refresh")
        self._token = r.get("token", self._token)
        return r

    # ── Tasks ───────────────────────────────────────────────────

    def create_task(self, title=None, project=None, **kwargs):
        body = {"title": title or f"Task_{_ID}_{id(self)}", "project": project or "Test"}
        body.update(kwargs)
        return self.api("POST", "/api/tasks", body)

    def get_task(self, task_id):
        return self.api("GET", f"/api/tasks/{task_id}")

    def update_task(self, task_id, **kwargs):
        return self.api("PUT", f"/api/tasks/{task_id}", kwargs)

    def delete_task(self, task_id):
        return _api_status("DELETE", f"/api/tasks/{task_id}", token=self.token)

    def restore_task(self, task_id):
        return self.api("POST", f"/api/tasks/{task_id}/restore")

    def purge_task(self, task_id):
        return _api_status("DELETE", f"/api/tasks/{task_id}/permanent", token=self.token)

    def list_tasks(self):
        return self.api("GET", "/api/tasks")

    def list_trash(self):
        return self.api("GET", "/api/tasks/trash")

    def search_tasks(self, q):
        return self.api("GET", f"/api/tasks/search?q={q}")

    def duplicate_task(self, task_id):
        return self.api("POST", f"/api/tasks/{task_id}/duplicate")

    def reorder_tasks(self, orders):
        return self.api("POST", "/api/tasks/reorder", {"orders": orders})

    def bulk_status(self, task_ids, status):
        return self.api("PUT", "/api/tasks/bulk-status", {"task_ids": task_ids, "status": status})

    def set_task_status(self, task_id, status):
        return self.update_task(task_id, status=status)

    # ── Comments ────────────────────────────────────────────────

    def add_comment(self, task_id, content="Test comment"):
        return self.api("POST", f"/api/tasks/{task_id}/comments", {"content": content})

    def list_comments(self, task_id):
        return self.api("GET", f"/api/tasks/{task_id}/comments")

    def edit_comment(self, comment_id, content):
        return self.api("PUT", f"/api/comments/{comment_id}", {"content": content})

    def delete_comment(self, comment_id):
        return _api_status("DELETE", f"/api/comments/{comment_id}", token=self.token)

    # ── Labels ──────────────────────────────────────────────────

    def create_label(self, name=None, color="#ff0000"):
        return self.api("POST", "/api/labels", {"name": name or f"Lbl_{_ID}", "color": color})

    def list_labels(self):
        return self.api("GET", "/api/labels")

    def delete_label(self, label_id):
        return _api_status("DELETE", f"/api/labels/{label_id}", token=self.token)

    def assign_label(self, task_id, label_id):
        return self.api("PUT", f"/api/tasks/{task_id}/labels/{label_id}")

    def remove_label(self, task_id, label_id):
        return _api_status("DELETE", f"/api/tasks/{task_id}/labels/{label_id}", token=self.token)

    def task_labels(self, task_id):
        return self.api("GET", f"/api/tasks/{task_id}/labels")

    # ── Dependencies ────────────────────────────────────────────

    def add_dependency(self, task_id, dep_id):
        return self.api("POST", f"/api/tasks/{task_id}/dependencies", {"dependency_id": dep_id})

    def remove_dependency(self, task_id, dep_id):
        return _api_status("DELETE", f"/api/tasks/{task_id}/dependencies/{dep_id}", token=self.token)

    def task_dependencies(self, task_id):
        return self.api("GET", f"/api/tasks/{task_id}/dependencies")

    def all_dependencies(self):
        return self.api("GET", "/api/dependencies")

    # ── Assignees ───────────────────────────────────────────────

    def assign_user(self, task_id, username):
        return self.api("POST", f"/api/tasks/{task_id}/assignees", {"username": username})

    def remove_assignee(self, task_id, username):
        return _api_status("DELETE", f"/api/tasks/{task_id}/assignees/{username}", token=self.token)

    def task_assignees(self, task_id):
        return self.api("GET", f"/api/tasks/{task_id}/assignees")

    # ── Watchers ────────────────────────────────────────────────

    def watch_task(self, task_id):
        return self.api("POST", f"/api/tasks/{task_id}/watch")

    def unwatch_task(self, task_id):
        return _api_status("DELETE", f"/api/tasks/{task_id}/watch", token=self.token)

    def task_watchers(self, task_id):
        return self.api("GET", f"/api/tasks/{task_id}/watchers")

    def watched_tasks(self):
        return self.api("GET", "/api/watched")

    # ── Time logging ────────────────────────────────────────────

    def log_time(self, task_id, hours=1.0, note=""):
        return self.api("POST", f"/api/tasks/{task_id}/time", {"hours": hours, "note": note})

    def task_time(self, task_id):
        return self.api("GET", f"/api/tasks/{task_id}/time")

    def task_time_summary(self, task_id):
        return self.api("GET", f"/api/tasks/{task_id}/time-summary")

    # ── Recurrence ──────────────────────────────────────────────

    def set_recurrence(self, task_id, pattern="daily", next_due="2026-06-01"):
        return self.api("PUT", f"/api/tasks/{task_id}/recurrence",
                         {"pattern": pattern, "next_due": next_due})

    def get_recurrence(self, task_id):
        return self.api("GET", f"/api/tasks/{task_id}/recurrence")

    def remove_recurrence(self, task_id):
        return _api_status("DELETE", f"/api/tasks/{task_id}/recurrence", token=self.token)

    # ── Sprints ─────────────────────────────────────────────────

    def create_sprint(self, name=None, start="2026-05-01", end="2026-05-15", **kwargs):
        body = {"name": name or f"Sprint_{_ID}", "start_date": start, "end_date": end}
        body.update(kwargs)
        return self.api("POST", "/api/sprints", body)

    def get_sprint(self, sprint_id):
        return self.api("GET", f"/api/sprints/{sprint_id}")

    def update_sprint(self, sprint_id, **kwargs):
        return self.api("PUT", f"/api/sprints/{sprint_id}", kwargs)

    def delete_sprint(self, sprint_id):
        return _api_status("DELETE", f"/api/sprints/{sprint_id}", token=self.token)

    def list_sprints(self):
        return self.api("GET", "/api/sprints")

    def start_sprint(self, sprint_id):
        return self.api("POST", f"/api/sprints/{sprint_id}/start")

    def complete_sprint(self, sprint_id):
        return self.api("POST", f"/api/sprints/{sprint_id}/complete")

    def add_sprint_tasks(self, sprint_id, task_ids):
        return self.api("POST", f"/api/sprints/{sprint_id}/tasks", {"task_ids": task_ids})

    def remove_sprint_task(self, sprint_id, task_id):
        return _api_status("DELETE", f"/api/sprints/{sprint_id}/tasks/{task_id}", token=self.token)

    def sprint_tasks(self, sprint_id):
        return self.api("GET", f"/api/sprints/{sprint_id}/tasks")

    def sprint_board(self, sprint_id):
        return self.api("GET", f"/api/sprints/{sprint_id}/board")

    def burn(self, sprint_id, task_id, points=1.0, hours=0.5):
        return self.api("POST", f"/api/sprints/{sprint_id}/burn",
                         {"task_id": task_id, "points": points, "hours": hours})

    def cancel_burn(self, sprint_id, burn_id):
        return self.api("DELETE", f"/api/sprints/{sprint_id}/burns/{burn_id}")

    def sprint_burns(self, sprint_id):
        return self.api("GET", f"/api/sprints/{sprint_id}/burns")

    def sprint_burndown(self, sprint_id):
        return self.api("GET", f"/api/sprints/{sprint_id}/burndown")

    def sprint_burn_summary(self, sprint_id):
        return self.api("GET", f"/api/sprints/{sprint_id}/burn-summary")

    def sprint_snapshot(self, sprint_id):
        return self.api("POST", f"/api/sprints/{sprint_id}/snapshot")

    def sprint_carryover(self, sprint_id):
        return self.api("POST", f"/api/sprints/{sprint_id}/carryover")

    def sprint_roots(self, sprint_id):
        return self.api("GET", f"/api/sprints/{sprint_id}/roots")

    def add_sprint_root(self, sprint_id, task_id):
        return self.api("POST", f"/api/sprints/{sprint_id}/roots", {"task_ids": [task_id]})

    def remove_sprint_root(self, sprint_id, task_id):
        return _api_status("DELETE", f"/api/sprints/{sprint_id}/roots/{task_id}", token=self.token)

    def sprint_scope(self, sprint_id):
        return self.api("GET", f"/api/sprints/{sprint_id}/scope")

    def sprint_compare(self, id_a, id_b):
        return self.api("GET", f"/api/sprints/compare?a={id_a}&b={id_b}")

    def velocity(self):
        return self.api("GET", "/api/sprints/velocity")

    def global_burndown(self):
        return self.api("GET", "/api/sprints/burndown")

    # ── Rooms ───────────────────────────────────────────────────

    def create_room(self, name=None, unit="points"):
        return self.api("POST", "/api/rooms", {"name": name or f"Room_{_ID}", "estimation_unit": unit})

    def get_room(self, room_id):
        return self.api("GET", f"/api/rooms/{room_id}")

    def list_rooms(self):
        return self.api("GET", "/api/rooms")

    def delete_room(self, room_id):
        return _api_status("DELETE", f"/api/rooms/{room_id}", token=self.token)

    def join_room(self, room_id):
        return self.api("POST", f"/api/rooms/{room_id}/join")

    def leave_room(self, room_id):
        return self.api("POST", f"/api/rooms/{room_id}/leave")

    def start_voting(self, room_id, task_id):
        return self.api("POST", f"/api/rooms/{room_id}/start-voting", {"task_id": task_id})

    def vote(self, room_id, value):
        return self.api("POST", f"/api/rooms/{room_id}/vote", {"value": value})

    def reveal_votes(self, room_id):
        return self.api("POST", f"/api/rooms/{room_id}/reveal")

    def accept_estimate(self, room_id, value):
        return self.api("POST", f"/api/rooms/{room_id}/accept", {"value": value})

    def close_room(self, room_id):
        return self.api("POST", f"/api/rooms/{room_id}/close")

    def remove_room_member(self, room_id, username):
        return _api_status("DELETE", f"/api/rooms/{room_id}/members/{username}", token=self.token)

    def set_room_role(self, room_id, username, role):
        return self.api("PUT", f"/api/rooms/{room_id}/role", {"username": username, "role": role})

    def export_room(self, room_id):
        return self.api("GET", f"/api/rooms/{room_id}/export")

    # ── Epics ───────────────────────────────────────────────────

    def create_epic(self, name=None):
        return self.api("POST", "/api/epics", {"name": name or f"Epic_{_ID}"})

    def get_epic(self, epic_id):
        return self.api("GET", f"/api/epics/{epic_id}")

    def list_epics(self):
        return self.api("GET", "/api/epics")

    def delete_epic(self, epic_id):
        return _api_status("DELETE", f"/api/epics/{epic_id}", token=self.token)

    def add_epic_tasks(self, epic_id, task_ids):
        return self.api("POST", f"/api/epics/{epic_id}/tasks", {"task_ids": task_ids})

    def remove_epic_task(self, epic_id, task_id):
        return _api_status("DELETE", f"/api/epics/{epic_id}/tasks/{task_id}", token=self.token)

    def epic_snapshot(self, epic_id):
        return self.api("POST", f"/api/epics/{epic_id}/snapshot")

    # ── Teams ───────────────────────────────────────────────────

    def create_team(self, name=None):
        return self.api("POST", "/api/teams", {"name": name or f"Team_{_ID}"})

    def get_team(self, team_id):
        return self.api("GET", f"/api/teams/{team_id}")

    def list_teams(self):
        return self.api("GET", "/api/teams")

    def delete_team(self, team_id):
        return _api_status("DELETE", f"/api/teams/{team_id}", token=self.token)

    def add_team_member(self, team_id, user_id):
        return self.api("POST", f"/api/teams/{team_id}/members", {"user_id": user_id})

    def remove_team_member(self, team_id, user_id):
        return _api_status("DELETE", f"/api/teams/{team_id}/members/{user_id}", token=self.token)

    def my_teams(self):
        return self.api("GET", "/api/me/teams")

    def team_scope(self, team_id):
        return self.api("GET", f"/api/teams/{team_id}/scope")

    def add_team_root(self, team_id, task_id):
        return self.api("POST", f"/api/teams/{team_id}/roots", {"task_id": task_id})

    def remove_team_root(self, team_id, task_id):
        return _api_status("DELETE", f"/api/teams/{team_id}/roots/{task_id}", token=self.token)

    # ── Templates ───────────────────────────────────────────────

    def create_template(self, name=None, data=None):
        return self.api("POST", "/api/templates", {
            "name": name or f"Tmpl_{_ID}",
            "data": data or {"title": "{{today}} standup", "project": "Daily"}
        })

    def list_templates(self):
        return self.api("GET", "/api/templates")

    def delete_template(self, template_id):
        return _api_status("DELETE", f"/api/templates/{template_id}", token=self.token)

    def instantiate_template(self, template_id):
        return self.api("POST", f"/api/templates/{template_id}/instantiate")

    # ── Webhooks ────────────────────────────────────────────────

    def create_webhook(self, url="https://example.com/hook", events="*", secret=None):
        body = {"url": url, "events": events}
        if secret:
            body["secret"] = secret
        return self.api("POST", "/api/webhooks", body)

    def list_webhooks(self):
        return self.api("GET", "/api/webhooks")

    def delete_webhook(self, webhook_id):
        return _api_status("DELETE", f"/api/webhooks/{webhook_id}", token=self.token)

    # ── Timer ───────────────────────────────────────────────────

    def start_timer(self, task_id=None):
        return self.api("POST", "/api/timer/start", {"task_id": task_id})

    def stop_timer(self):
        return self.api("POST", "/api/timer/stop")

    def pause_timer(self):
        return self.api("POST", "/api/timer/pause")

    def resume_timer(self):
        return self.api("POST", "/api/timer/resume")

    def skip_timer(self):
        return self.api("POST", "/api/timer/skip")

    def timer_state(self):
        return self.api("GET", "/api/timer")

    def timer_active(self):
        return self.api("GET", "/api/timer/active")

    def timer_ticket(self):
        return self.api("POST", "/api/timer/ticket")

    # ── Config ──────────────────────────────────────────────────

    def get_config(self):
        return self.api("GET", "/api/config")

    def update_config(self, **kwargs):
        cfg = self.get_config()
        cfg.update(kwargs)
        return self.api("PUT", "/api/config", cfg)

    # ── History / Stats / Export ─────────────────────────────────

    def history(self):
        return self.api("GET", "/api/history")

    def stats(self):
        return self.api("GET", "/api/stats")

    def export_sessions(self, fmt="json"):
        return self.api("GET", f"/api/export/sessions?format={fmt}")

    def export_tasks(self):
        return self.api("GET", "/api/export/tasks")

    def export_burns(self, sprint_id):
        return self.api("GET", f"/api/export/burns/{sprint_id}")

    def import_tasks_json(self, tasks):
        return self.api("POST", "/api/import/tasks/json", {"tasks": tasks})

    # ── Admin ───────────────────────────────────────────────────

    def admin_users(self):
        return self.api("GET", "/api/admin/users")

    def admin_set_role(self, user_id, role):
        return self.api("PUT", f"/api/admin/users/{user_id}/role", {"role": role})

    def admin_reset_password(self, user_id, password):
        return self.api("PUT", f"/api/admin/users/{user_id}/password", {"password": password})

    def admin_delete_user(self, user_id):
        return _api_status("DELETE", f"/api/admin/users/{user_id}", token=self.token)

    def admin_backup(self):
        return self.api("POST", "/api/admin/backup")

    def admin_backups(self):
        return self.api("GET", "/api/admin/backups")

    def admin_restore(self, backup_name):
        return self.api("POST", "/api/admin/restore", {"name": backup_name})

    # ── Profile ─────────────────────────────────────────────────

    def update_profile(self, **kwargs):
        return self.api("PUT", "/api/profile", kwargs)

    def get_notif_prefs(self):
        return self.api("GET", "/api/profile/notifications")

    def update_notif_prefs(self, prefs):
        return self.api("PUT", "/api/profile/notifications", prefs)

    # ── Notifications ───────────────────────────────────────────

    def notifications(self):
        return self.api("GET", "/api/notifications")

    def unread_count(self):
        return self.api("GET", "/api/notifications/unread")

    def mark_read(self):
        return self.api("POST", "/api/notifications/read")

    # ── Misc ────────────────────────────────────────────────────

    def health(self):
        return _api("GET", "/api/health")

    def audit(self):
        return self.api("GET", "/api/audit")

    def users(self):
        return self.api("GET", "/api/users")

    def assignees_list(self):
        return self.api("GET", "/api/assignees")

    def burn_totals(self):
        return self.api("GET", "/api/burn-totals")

    def user_hours(self):
        return self.api("GET", "/api/reports/user-hours")

    def task_sprints(self):
        return self.api("GET", "/api/task-sprints")

    def update_session_note(self, session_id, note):
        return self.api("PUT", f"/api/sessions/{session_id}/note", {"note": note})

    # ── GUI assertions ──────────────────────────────────────────

    @staticmethod
    def assert_task_in_gui(app, title):
        from harness import click_tab
        click_tab(app, "Timer")
        click_tab(app, "Tasks")
        assert title in app.page_source(), f"Task '{title}' not found in GUI"

    @staticmethod
    def assert_sprint_status(app, name, status):
        from harness import click_tab
        click_tab(app, "Timer")
        click_tab(app, "Sprints")
        src = app.page_source()
        assert name in src, f"Sprint '{name}' not in GUI"
        assert status in src, f"Status '{status}' not in GUI for sprint '{name}'"

    @staticmethod
    def assert_timer_state(app, *expected_texts):
        from harness import click_tab
        click_tab(app, "Timer")
        body = app.text(app.find("body"))
        assert any(t in body for t in expected_texts), \
            f"Expected one of {expected_texts} in timer, got: {body[:200]}"


def get_uid(username):
    """Get user ID by username."""
    root = H()
    users = root.admin_users()
    for u in users:
        if u["username"] == username:
            return u["id"]
    raise ValueError(f"User '{username}' not found")
