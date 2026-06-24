"""Phase 47 / E-4 Step 2: the scheduled re-analysis loop -- the "monitoring"
half that makes the watchlist an actual early-warning feed instead of a
passive bookmark list. find_due_companies/trigger_refresh are the testable
pieces (same split as reaper.py: the infinite loop itself isn't unit tested
directly, only what it calls each tick).
"""

import uuid
from datetime import datetime
from unittest.mock import AsyncMock

import app.tasks.watchlist_refresher as refresher_module
from app.models.analysis_result import AnalysisResult
from app.tasks.watchlist_refresher import (
    MAX_REFRESHES_PER_TICK,
    STALE_AFTER_HOURS,
    _due_companies_query,
    find_due_companies,
    trigger_refresh,
)


class FakeResult:
    def __init__(self, rows):
        self._rows = rows

    def all(self):
        return self._rows


class FakeSession:
    def __init__(self, execute_rows=None):
        self._execute_rows = execute_rows or []
        self.added = []
        self.committed = False
        self.refreshed = []

    async def execute(self, stmt):
        return FakeResult(self._execute_rows)

    def add(self, obj):
        self.added.append(obj)
        if getattr(obj, "id", None) is None:
            obj.id = uuid.uuid4()  # simulates the real flush-time column default

    async def commit(self):
        self.committed = True

    async def refresh(self, obj):
        self.refreshed.append(obj)


def test_due_companies_query_joins_watchlist_and_filters_stale_or_never_analyzed():
    sql = str(_due_companies_query(datetime(2026, 6, 23, 0, 0, 0)))

    assert "JOIN watchlist" in sql
    assert "companies.last_analyzed IS NULL" in sql
    assert "companies.last_analyzed <" in sql
    assert " OR " in sql
    assert "DISTINCT" in sql
    assert "ORDER BY companies.last_analyzed" in sql
    assert "LIMIT" in sql


async def test_find_due_companies_extracts_company_ids_from_rows():
    id1, id2 = uuid.uuid4(), uuid.uuid4()
    session = FakeSession(execute_rows=[(id1, None), (id2, datetime(2026, 6, 1))])

    due = await find_due_companies(session)

    assert due == [id1, id2]


async def test_find_due_companies_is_empty_when_nothing_is_due():
    session = FakeSession(execute_rows=[])

    due = await find_due_companies(session)

    assert due == []


async def test_trigger_refresh_creates_pending_analysis_and_invokes_run_full_analysis(monkeypatch):
    run_mock = AsyncMock()
    monkeypatch.setattr(refresher_module, "run_full_analysis", run_mock)
    session = FakeSession()
    company_id = uuid.uuid4()

    await trigger_refresh(session, company_id)

    assert len(session.added) == 1
    analysis = session.added[0]
    assert isinstance(analysis, AnalysisResult)
    assert analysis.company_id == company_id
    assert analysis.status == "pending"
    assert session.committed is True
    assert session.refreshed == [analysis]
    run_mock.assert_awaited_once_with(company_id, analysis.id)


def test_stale_after_hours_is_at_least_a_day():
    # Anything shorter risks burning the shared Gemini/yfinance budget on
    # companies a human hasn't even looked at recently.
    assert STALE_AFTER_HOURS >= 24


def test_max_refreshes_per_tick_is_small():
    # A large watchlist backlog must drain gradually, not burst all at once.
    assert 1 <= MAX_REFRESHES_PER_TICK <= 10
