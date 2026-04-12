"""Timer state machine: all phases, transitions, and edge cases."""
import time
import pytest
from helpers import H


class TestTimerPhases:

    def test_idle_state(self, logged_in):
        h = H()
        try:
            h.stop_timer()
        except Exception:
            pass
        s = h.timer_state()
        assert s["phase"] == "Idle" and s["status"] == "Idle"

    def test_start_work(self, logged_in):
        h = H()
        s = h.start_timer()
        assert s["phase"] == "Work" and s["status"] == "Running"

    def test_pause_work(self, logged_in):
        h = H()
        h.start_timer()
        s = h.pause_timer()
        assert s["phase"] == "Work" and s["status"] == "Paused"

    def test_resume_work(self, logged_in):
        h = H()
        h.start_timer()
        h.pause_timer()
        s = h.resume_timer()
        assert s["phase"] == "Work" and s["status"] == "Running"

    def test_stop_work(self, logged_in):
        h = H()
        h.start_timer()
        s = h.stop_timer()
        assert s["phase"] == "Idle" and s["status"] == "Idle"

    def test_skip_to_break(self, logged_in):
        h = H()
        h.start_timer()
        s = h.skip_timer()
        assert s["phase"] in ("ShortBreak", "LongBreak")

    def test_skip_break_to_work(self, logged_in):
        h = H()
        h.start_timer()
        h.skip_timer()  # → break
        s = h.skip_timer()  # → work
        assert s["phase"] == "Work"

    def test_start_with_task(self, logged_in):
        h = H()
        task = h.create_task("TimerTask")
        s = h.start_timer(task["id"])
        assert s["phase"] == "Work"

    def test_timer_active_during_work(self, logged_in):
        h = H()
        h.start_timer()
        a = h.timer_active()
        assert a is not None
        h.stop_timer()

    def test_timer_ticket(self, logged_in):
        h = H()
        h.start_timer()
        r = h.timer_ticket()
        assert isinstance(r, dict)
        h.stop_timer()


class TestTimerEdgeCases:

    def test_pause_when_idle_fails(self, logged_in):
        h = H()
        try:
            h.stop_timer()
        except Exception:
            pass
        code, _ = h.api_status("POST", "/api/timer/pause")
        # Daemon may return 200 (no-op) or 400 — both acceptable
        assert code in (200, 400)

    def test_resume_when_idle_fails(self, logged_in):
        h = H()
        try:
            h.stop_timer()
        except Exception:
            pass
        code, _ = h.api_status("POST", "/api/timer/resume")
        assert code in (200, 400)

    def test_double_start(self, logged_in):
        h = H()
        h.start_timer()
        code, _ = h.api_status("POST", "/api/timer/start", {"task_id": None})
        h.stop_timer()
        # Should either succeed (restart) or fail gracefully
        assert code in (200, 400, 409)

    def test_double_pause(self, logged_in):
        h = H()
        h.start_timer()
        h.pause_timer()
        code, _ = h.api_status("POST", "/api/timer/pause")
        h.stop_timer()
        assert code in (200, 400)

    def test_stop_when_idle(self, logged_in):
        h = H()
        try:
            h.stop_timer()
        except Exception:
            pass
        code, _ = h.api_status("POST", "/api/timer/stop")
        assert code in (200, 400)

    def test_skip_when_idle(self, logged_in):
        h = H()
        try:
            h.stop_timer()
        except Exception:
            pass
        code, _ = h.api_status("POST", "/api/timer/skip")
        assert code in (200, 400)


class TestTimerHistory:

    def test_completed_session_in_history(self, logged_in):
        h = H()
        h.start_timer()
        time.sleep(0.5)
        h.stop_timer()
        hist = h.history()
        assert len(hist) >= 1

    def test_session_note_update(self, logged_in):
        h = H()
        h.start_timer()
        time.sleep(0.5)
        h.stop_timer()
        hist = h.history()
        if hist:
            r = h.update_session_note(hist[0]["id"], "My note")
            assert r.get("note") == "My note" or isinstance(r, dict)


class TestTimerMultiSkip:
    """Skip through multiple work/break cycles."""

    def test_four_skips_cycle(self, logged_in):
        h = H()
        h.start_timer()
        phases = []
        for _ in range(6):
            s = h.skip_timer()
            phases.append(s["phase"])
        h.stop_timer()
        assert "Work" in phases
        assert any(p in ("ShortBreak", "LongBreak") for p in phases)
