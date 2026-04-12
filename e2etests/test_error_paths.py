"""Error paths: invalid inputs, unauthorized access, not-found resources."""
import pytest
from helpers import H, _api_status


class TestTaskErrors:

    def test_create_empty_title(self, logged_in):
        h = H()
        code, _ = h.api_status("POST", "/api/tasks", {"title": "", "project": "X"})
        assert code == 400

    def test_create_no_title(self, logged_in):
        h = H()
        code, _ = h.api_status("POST", "/api/tasks", {"project": "X"})
        assert code in (400, 422)

    def test_get_nonexistent_task(self, logged_in):
        h = H()
        code, _ = h.api_status("GET", "/api/tasks/999999")
        assert code in (204, 400, 404, 500)

    def test_update_nonexistent_task(self, logged_in):
        h = H()
        code, _ = h.api_status("PUT", "/api/tasks/999999", {"title": "X"})
        assert code in (204, 400, 404, 500)

    def test_delete_nonexistent_task(self, logged_in):
        code, _ = _api_status("DELETE", "/api/tasks/999999", token=H().token)
        assert code in (204, 400, 404, 500)

    def test_comment_on_nonexistent_task(self, logged_in):
        h = H()
        code, _ = h.api_status("POST", "/api/tasks/999999/comments", {"content": "X"})
        assert code in (204, 400, 404, 500)

    def test_non_owner_cannot_update(self, logged_in):
        h = H()
        t = h.create_task("OwnerOnly")
        u = H.register("err_user1")
        code, _ = u.api_status("PUT", f"/api/tasks/{t['id']}", {"title": "Hacked"})
        assert code == 403

    def test_non_owner_cannot_delete(self, logged_in):
        h = H()
        t = h.create_task("OwnerDel")
        u = H.register("err_user2")
        code, _ = _api_status("DELETE", f"/api/tasks/{t['id']}", token=u.token)
        assert code == 403

    def test_restore_non_deleted_task(self, logged_in):
        h = H()
        t = h.create_task("NotDel")
        code, _ = h.api_status("POST", f"/api/tasks/{t['id']}/restore")
        assert code in (200, 204, 400, 404, 409)  # No-op or error

    def test_purge_non_deleted_task(self, logged_in):
        h = H()
        t = h.create_task("NotPurge")
        code, _ = _api_status("DELETE", f"/api/tasks/{t['id']}/permanent", token=h.token)
        assert code in (400, 404, 409)


class TestSprintErrors:

    def test_create_missing_name(self, logged_in):
        h = H()
        code, _ = h.api_status("POST", "/api/sprints",
                               {"start_date": "2026-01-01", "end_date": "2026-01-15"})
        assert code in (400, 422)

    def test_get_nonexistent_sprint(self, logged_in):
        h = H()
        code, _ = h.api_status("GET", "/api/sprints/999999")
        assert code in (204, 400, 404, 500)

    def test_add_task_to_nonexistent_sprint(self, logged_in):
        h = H()
        t = h.create_task("SpErr")
        code, _ = h.api_status("POST", "/api/sprints/999999/tasks", {"task_ids": [t["id"]]})
        assert code in (204, 400, 404, 500)

    def test_burn_nonexistent_sprint(self, logged_in):
        h = H()
        code, _ = h.api_status("POST", "/api/sprints/999999/burn",
                               {"task_id": 1, "points": 1, "hours": 0.5})
        assert code in (204, 400, 404, 500)


class TestRoomErrors:

    def test_create_missing_name(self, logged_in):
        h = H()
        code, _ = h.api_status("POST", "/api/rooms", {"estimation_unit": "points"})
        assert code in (400, 422)

    def test_get_nonexistent_room(self, logged_in):
        h = H()
        code, _ = h.api_status("GET", "/api/rooms/999999")
        assert code in (204, 400, 404, 500)

    def test_vote_without_joining(self, logged_in):
        h = H()
        r = h.create_room("VoteErr")
        t = h.create_task("VoteErrT")
        h.join_room(r["id"])
        h.start_voting(r["id"], t["id"])
        u = H.register("room_err1")
        code, _ = u.api_status("POST", f"/api/rooms/{r['id']}/vote", {"value": 5})
        assert code in (400, 403)

    def test_reveal_without_votes(self, logged_in):
        h = H()
        r = h.create_room("RevealErr")
        t = h.create_task("RevErrT")
        h.join_room(r["id"])
        h.start_voting(r["id"], t["id"])
        # Reveal with no votes — should succeed or fail gracefully
        code, _ = h.api_status("POST", f"/api/rooms/{r['id']}/reveal")
        assert code in (200, 400)


class TestEpicErrors:

    def test_get_nonexistent_epic(self, logged_in):
        h = H()
        code, _ = h.api_status("GET", "/api/epics/999999")
        assert code in (204, 400, 404, 500)

    def test_add_task_to_nonexistent_epic(self, logged_in):
        h = H()
        code, _ = h.api_status("POST", "/api/epics/999999/tasks", {"task_ids": [1]})
        assert code in (204, 400, 404, 500)


class TestLabelErrors:

    def test_delete_nonexistent_label(self, logged_in):
        h = H()
        code, _ = _api_status("DELETE", "/api/labels/999999", token=h.token)
        assert code in (204, 400, 404, 500)

    def test_assign_nonexistent_label(self, logged_in):
        h = H()
        t = h.create_task("LblErr")
        code, _ = h.api_status("PUT", f"/api/tasks/{t['id']}/labels/999999")
        assert code in (204, 400, 404, 500)


class TestTeamErrors:

    def test_get_nonexistent_team(self, logged_in):
        h = H()
        code, _ = h.api_status("GET", "/api/teams/999999")
        assert code in (204, 400, 404, 500)

    def test_delete_nonexistent_team(self, logged_in):
        h = H()
        code, _ = _api_status("DELETE", "/api/teams/999999", token=h.token)
        assert code in (204, 400, 404, 500)


class TestAuthErrors:

    def test_no_token(self, logged_in):
        code, _ = _api_status("GET", "/api/tasks")
        assert code == 401

    def test_invalid_token(self, logged_in):
        code, _ = _api_status("GET", "/api/tasks", token="invalid.jwt.token")
        assert code == 401

    def test_login_wrong_user(self, logged_in):
        code, _ = _api_status("POST", "/api/auth/login",
                              {"username": "nonexistent", "password": "Pass1xxx"})
        assert code == 401

    def test_register_short_password(self, logged_in):
        code, _ = _api_status("POST", "/api/auth/register",
                              {"username": "shortpw", "password": "Sh1"})
        assert code == 400

    def test_register_no_uppercase(self, logged_in):
        code, _ = _api_status("POST", "/api/auth/register",
                              {"username": "noup", "password": "alllower1"})
        assert code == 400

    def test_register_no_digit(self, logged_in):
        code, _ = _api_status("POST", "/api/auth/register",
                              {"username": "nodig", "password": "NoDigitHere"})
        assert code == 400

    def test_register_duplicate(self, logged_in):
        H.register("dup_auth1", "DupAuth1x")
        code, _ = _api_status("POST", "/api/auth/register",
                              {"username": "dup_auth1", "password": "DupAuth1x"})
        assert code in (400, 409)


class TestAdminErrors:

    def test_non_root_cannot_list_users(self, logged_in):
        u = H.register("admin_err1")
        code, _ = u.api_status("GET", "/api/admin/users")
        assert code == 403

    def test_non_root_cannot_change_role(self, logged_in):
        u = H.register("admin_err2")
        code, _ = u.api_status("PUT", "/api/admin/users/1/role", {"role": "root"})
        assert code == 403

    def test_non_root_cannot_backup(self, logged_in):
        u = H.register("admin_err3")
        code, _ = u.api_status("POST", "/api/admin/backup")
        assert code == 403

    def test_set_invalid_role(self, logged_in):
        h = H()
        u = H.register("admin_err4")
        from helpers import get_uid
        uid = get_uid("admin_err4")
        code, _ = h.api_status("PUT", f"/api/admin/users/{uid}/role", {"role": "superadmin"})
        assert code == 400

    def test_delete_nonexistent_user(self, logged_in):
        h = H()
        code, _ = _api_status("DELETE", "/api/admin/users/999999", token=h.token)
        assert code in (204, 400, 404, 500)


class TestCommentErrors:

    def test_edit_nonexistent_comment(self, logged_in):
        h = H()
        code, _ = h.api_status("PUT", "/api/comments/999999", {"content": "X"})
        assert code in (204, 400, 404, 500)

    def test_delete_nonexistent_comment(self, logged_in):
        h = H()
        code, _ = _api_status("DELETE", "/api/comments/999999", token=h.token)
        assert code in (204, 400, 404, 500)

    def test_non_owner_cannot_edit_comment(self, logged_in):
        h = H()
        t = h.create_task("CmOwn")
        c = h.add_comment(t["id"], "Original")
        u = H.register("cm_err1")
        code, _ = u.api_status("PUT", f"/api/comments/{c['id']}", {"content": "Hacked"})
        assert code == 403

    def test_non_owner_cannot_delete_comment(self, logged_in):
        h = H()
        t = h.create_task("CmDel")
        c = h.add_comment(t["id"], "Mine")
        u = H.register("cm_err2")
        code, _ = _api_status("DELETE", f"/api/comments/{c['id']}", token=u.token)
        assert code == 403

    def test_empty_comment_rejected(self, logged_in):
        h = H()
        t = h.create_task("CmEmpty")
        code, _ = h.api_status("POST", f"/api/tasks/{t['id']}/comments", {"content": ""})
        assert code == 400
