"""Stuck-analysis reaper (Phase 10 Step 3, OPUS_ARCHITECTURAL_REVIEW.md Sec.8 item 3 /
ADR-012): a Render free-tier spin-down/restart can kill the in-process background
task mid-analysis, leaving an AnalysisResult frozen at running:<stage> forever. The
reaper marks such rows with the new terminal "error" status -- it must NOT revive the
retired "failed" status (ADR-010 / Phase 3).

Phase 40 (H-1 / A-2): the reaper now also catches rows frozen at "pending" (a task
lost before the worker ever started), via a single atomic conditional UPDATE rather
than a SELECT-then-mutate-then-commit -- eliminating the race where a worker
completing an analysis between the reaper's scan and its write could be clobbered
back to "error".
"""

from datetime import datetime, timedelta, timezone

import app.tasks.reaper as reaper_module
from app.tasks.reaper import _stuck_analyses_update, get_reaper_status, reap_stuck_analyses


class FakeUpdateResult:
    def __init__(self, rowcount):
        self.rowcount = rowcount


class FakeSession:
    def __init__(self, rowcount):
        self.rowcount = rowcount
        self.committed = False
        self.executed = None

    async def execute(self, query):
        self.executed = query
        return FakeUpdateResult(self.rowcount)

    async def commit(self):
        self.committed = True


def test_stuck_analyses_update_targets_running_and_pending_status_past_cutoff():
    cutoff = datetime(2026, 6, 16, 12, 0, 0)
    sql = str(_stuck_analyses_update(cutoff))

    assert "UPDATE analysis_results" in sql
    assert "analysis_results.status LIKE" in sql
    assert "analysis_results.status =" in sql
    assert " OR " in sql
    assert "analysis_results.run_at" in sql


async def test_reap_stuck_analyses_marks_stale_rows_as_error():
    session = FakeSession(rowcount=2)

    count = await reap_stuck_analyses(session)

    assert count == 2
    assert session.committed is True


async def test_reap_stuck_analyses_is_noop_when_nothing_stuck():
    session = FakeSession(rowcount=0)

    count = await reap_stuck_analyses(session)

    assert count == 0
    assert session.committed is True


def test_reaper_status_is_stale_before_any_run(monkeypatch):
    monkeypatch.setattr(reaper_module, "_last_run_at", None)

    status = get_reaper_status()

    assert status["stale"] is True
    assert status["last_run_at"] is None


def test_reaper_status_is_fresh_immediately_after_a_run(monkeypatch):
    monkeypatch.setattr(reaper_module, "_last_run_at", datetime.now(timezone.utc))
    monkeypatch.setattr(reaper_module, "_last_reaped_count", 3)

    status = get_reaper_status()

    assert status["stale"] is False
    assert status["last_reaped_count"] == 3
    assert status["last_run_at"] is not None


def test_reaper_status_is_stale_after_the_grace_window(monkeypatch):
    too_long_ago = datetime.now(timezone.utc) - timedelta(seconds=reaper_module._STALE_AFTER_SECONDS + 1)
    monkeypatch.setattr(reaper_module, "_last_run_at", too_long_ago)

    status = get_reaper_status()

    assert status["stale"] is True


def test_reaper_status_is_fresh_just_inside_the_grace_window(monkeypatch):
    just_in_time = datetime.now(timezone.utc) - timedelta(seconds=reaper_module._STALE_AFTER_SECONDS - 5)
    monkeypatch.setattr(reaper_module, "_last_run_at", just_in_time)

    status = get_reaper_status()

    assert status["stale"] is False
