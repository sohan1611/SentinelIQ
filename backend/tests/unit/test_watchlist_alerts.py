"""Phase 47 / E-4 Step 1, Phase 48 / A-1 Step 1: _generate_watchlist_alerts --
the detector half of watchlist monitoring. Runs at the end of every
completed analysis and alerts every user watching the company IF the new
score crosses a risk band (FraudScorer.classify_risk) relative to the
company's previous completed analysis. Same-band changes, a missing prior
analysis, or a missing score are all "nothing to report", not errors.

Phase 48 (A-1): the function now opens its own fresh session internally
rather than accepting one via a StageContext, so tests monkeypatch
AsyncSessionLocal -- same pattern as test_analysis_pipeline.py's
patch_session fixture -- instead of constructing a StageContext.
"""

import logging
import uuid

import app.tasks.analysis_worker as analysis_worker
from app.models.analysis_result import AnalysisResult
from app.models.watchlist_alert import WatchlistAlert
from app.tasks.analysis_worker import _generate_watchlist_alerts

LOG = logging.getLogger("test_watchlist_alerts")


class FakeScalars:
    def __init__(self, items):
        self._items = items

    def first(self):
        return self._items[0] if self._items else None

    def all(self):
        return list(self._items)


class FakeResult:
    def __init__(self, items):
        self._items = items

    def scalars(self):
        return FakeScalars(self._items)


class FakeSession:
    """`current_analysis` backs the initial session.get() lookup. Each entry
    in `call_results` is the item-list for one .execute() call, consumed in
    order -- _generate_watchlist_alerts issues at most 2 (previous-analysis
    lookup, then watcher-id lookup), in that order."""

    def __init__(self, current_analysis, *call_results):
        self._current_analysis = current_analysis
        self._call_results = list(call_results)
        self._call_index = 0
        self.added = []
        self.committed = False

    async def get(self, model, id_):
        return self._current_analysis

    async def execute(self, stmt):
        items = self._call_results[self._call_index] if self._call_index < len(self._call_results) else []
        self._call_index += 1
        return FakeResult(items)

    def add(self, obj):
        self.added.append(obj)

    async def commit(self):
        self.committed = True


class FakeSessionCtx:
    def __init__(self, session):
        self._session = session

    async def __aenter__(self):
        return self._session

    async def __aexit__(self, exc_type, exc, tb):
        return False


def _previous(score, company_id=None):
    return AnalysisResult(id=uuid.uuid4(), company_id=company_id or uuid.uuid4(), integrity_score=score, status="complete")


def _patch_session(monkeypatch, session):
    monkeypatch.setattr(analysis_worker, "AsyncSessionLocal", lambda: FakeSessionCtx(session))


async def test_band_crossing_creates_one_alert_per_watcher(monkeypatch):
    watcher_a, watcher_b = uuid.uuid4(), uuid.uuid4()
    analysis_id, company_id = uuid.uuid4(), uuid.uuid4()
    current = AnalysisResult(id=analysis_id, company_id=company_id, integrity_score=55.0, status="complete")
    # 85.0 -> "strong", 55.0 -> "moderate": a real band crossing.
    session = FakeSession(current, [_previous(85.0, company_id)], [watcher_a, watcher_b])
    _patch_session(monkeypatch, session)

    await _generate_watchlist_alerts(analysis_id, company_id, LOG)

    assert len(session.added) == 2
    assert all(isinstance(a, WatchlistAlert) for a in session.added)
    assert {a.user_id for a in session.added} == {watcher_a, watcher_b}
    for alert in session.added:
        assert alert.previous_score == 85.0
        assert alert.new_score == 55.0
        assert alert.previous_risk == "strong"
        assert alert.new_risk == "moderate"
        assert alert.company_id == company_id
        assert alert.analysis_id == analysis_id
    assert session.committed is True


async def test_same_band_creates_no_alert(monkeypatch):
    analysis_id, company_id = uuid.uuid4(), uuid.uuid4()
    # 85.0 and 82.0 are both "strong" -- no crossing.
    current = AnalysisResult(id=analysis_id, company_id=company_id, integrity_score=82.0, status="complete")
    session = FakeSession(current, [_previous(85.0, company_id)], [uuid.uuid4()])
    _patch_session(monkeypatch, session)

    await _generate_watchlist_alerts(analysis_id, company_id, LOG)

    assert session.added == []
    assert session.committed is False


async def test_no_previous_analysis_creates_no_alert(monkeypatch):
    analysis_id, company_id = uuid.uuid4(), uuid.uuid4()
    current = AnalysisResult(id=analysis_id, company_id=company_id, integrity_score=55.0, status="complete")
    session = FakeSession(current, [], [uuid.uuid4()])  # first call: no prior row
    _patch_session(monkeypatch, session)

    await _generate_watchlist_alerts(analysis_id, company_id, LOG)

    assert session.added == []
    assert session.committed is False


async def test_missing_previous_score_is_skipped_not_crashed(monkeypatch):
    analysis_id, company_id = uuid.uuid4(), uuid.uuid4()
    current = AnalysisResult(id=analysis_id, company_id=company_id, integrity_score=55.0, status="complete")
    session = FakeSession(current, [_previous(None, company_id)], [uuid.uuid4()])
    _patch_session(monkeypatch, session)

    await _generate_watchlist_alerts(analysis_id, company_id, LOG)  # must not raise

    assert session.added == []
    assert session.committed is False


async def test_missing_current_analysis_is_skipped_not_crashed(monkeypatch):
    # New edge case introduced by Phase 48 (A-1): the function now fetches
    # its own AnalysisResult rather than trusting an already-validated
    # object handed to it, so a not-found row must degrade gracefully too.
    analysis_id, company_id = uuid.uuid4(), uuid.uuid4()
    session = FakeSession(None, [_previous(85.0, company_id)], [uuid.uuid4()])
    _patch_session(monkeypatch, session)

    await _generate_watchlist_alerts(analysis_id, company_id, LOG)  # must not raise

    assert session.added == []
    assert session.committed is False


async def test_missing_current_score_is_skipped_not_crashed(monkeypatch):
    analysis_id, company_id = uuid.uuid4(), uuid.uuid4()
    current = AnalysisResult(id=analysis_id, company_id=company_id, integrity_score=None, status="complete")
    session = FakeSession(current, [_previous(85.0, company_id)], [uuid.uuid4()])
    _patch_session(monkeypatch, session)

    await _generate_watchlist_alerts(analysis_id, company_id, LOG)  # must not raise

    assert session.added == []
    assert session.committed is False


async def test_no_watchers_creates_no_alert_and_no_commit(monkeypatch):
    analysis_id, company_id = uuid.uuid4(), uuid.uuid4()
    current = AnalysisResult(id=analysis_id, company_id=company_id, integrity_score=55.0, status="complete")
    # Band crosses, but nobody is watching this company.
    session = FakeSession(current, [_previous(85.0, company_id)], [])
    _patch_session(monkeypatch, session)

    await _generate_watchlist_alerts(analysis_id, company_id, LOG)

    assert session.added == []
    assert session.committed is False
