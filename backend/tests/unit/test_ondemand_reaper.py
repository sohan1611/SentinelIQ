from datetime import datetime, timedelta, timezone

from app.config import settings
from app.tasks import reaper


class FakeResult:
    def __init__(self, rowcount: int):
        self.rowcount = rowcount


class FakeSession:
    def __init__(self, rowcount: int = 0):
        self.rowcount = rowcount
        self.execute_calls = 0
        self.commit_calls = 0

    async def execute(self, *args, **kwargs):
        self.execute_calls += 1
        return FakeResult(self.rowcount)

    async def commit(self):
        self.commit_calls += 1


async def test_maybe_reap_stuck_analyses_reaps_on_first_call(monkeypatch):
    session = FakeSession(rowcount=2)
    monkeypatch.setattr(reaper, "_last_ondemand_reap_at", None)
    monkeypatch.setattr(reaper, "_last_run_at", None)

    result = await reaper.maybe_reap_stuck_analyses(session)

    assert result == 2
    assert session.execute_calls == 1
    assert session.commit_calls == 1


async def test_maybe_reap_stuck_analyses_throttles_immediate_second_call(monkeypatch):
    session = FakeSession(rowcount=1)
    monkeypatch.setattr(reaper, "_last_ondemand_reap_at", None)

    assert await reaper.maybe_reap_stuck_analyses(session) == 1
    assert await reaper.maybe_reap_stuck_analyses(session) is None
    assert session.execute_calls == 1
    assert session.commit_calls == 1


async def test_maybe_reap_stuck_analyses_reaps_after_throttle_window(monkeypatch):
    session = FakeSession(rowcount=3)
    older_than_window = datetime.now(timezone.utc) - timedelta(
        seconds=reaper.REAP_MIN_INTERVAL_SECONDS + 1
    )
    monkeypatch.setattr(reaper, "_last_ondemand_reap_at", older_than_window)

    result = await reaper.maybe_reap_stuck_analyses(session)

    assert result == 3
    assert session.execute_calls == 1


async def test_maybe_reap_stuck_analyses_updates_reaper_health(monkeypatch):
    session = FakeSession()
    monkeypatch.setattr(reaper, "_last_ondemand_reap_at", None)
    monkeypatch.setattr(reaper, "_last_run_at", None)

    await reaper.maybe_reap_stuck_analyses(session)

    assert reaper._last_run_at is not None


def test_get_reaper_status_reports_safe_mode_as_not_stale(monkeypatch):
    monkeypatch.setattr(reaper, "_last_run_at", None)
    monkeypatch.setattr(settings, "ENABLE_REAPER_LOOP", False)

    status = reaper.get_reaper_status()

    assert status["loop_enabled"] is False
    assert status["stale"] is False
