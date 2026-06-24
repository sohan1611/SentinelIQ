"""Phase 47 / E-4 Step 1: _generate_watchlist_alerts(ctx) -- the detector half
of watchlist monitoring. Runs at the end of every completed analysis and
alerts every user watching the company IF the new score crosses a risk band
(FraudScorer.classify_risk) relative to the company's previous completed
analysis. Same-band changes, a missing prior analysis, or a missing score
are all "nothing to report", not errors.

Uses this codebase's established FakeSession double (see test_reaper.py /
test_analysis_pipeline.py) rather than a real DB connection.
"""

import logging
import uuid

import pytest

from app.models.analysis_result import AnalysisResult
from app.models.watchlist_alert import WatchlistAlert
from app.tasks.analysis_worker import StageContext, _generate_watchlist_alerts

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
    """Each entry in `call_results` is the item-list for one .execute() call,
    consumed in order -- _generate_watchlist_alerts issues at most 2 calls
    (previous-analysis lookup, then watcher-id lookup), in that order."""

    def __init__(self, *call_results):
        self._call_results = list(call_results)
        self._call_index = 0
        self.added = []
        self.committed = False
        self.rolled_back = False

    async def execute(self, stmt):
        items = self._call_results[self._call_index] if self._call_index < len(self._call_results) else []
        self._call_index += 1
        return FakeResult(items)

    def add(self, obj):
        self.added.append(obj)

    async def commit(self):
        self.committed = True

    async def rollback(self):
        self.rolled_back = True


def _ctx(session, analysis_score, company_id=None, analysis_id=None):
    company_id = company_id or uuid.uuid4()
    analysis_id = analysis_id or uuid.uuid4()
    analysis = AnalysisResult(id=analysis_id, company_id=company_id, integrity_score=analysis_score, status="complete")
    return StageContext(
        session=session,
        company=None,
        analysis=analysis,
        analysis_id=analysis_id,
        company_id=company_id,
        log=LOG,
    )


def _previous(score, company_id=None):
    return AnalysisResult(id=uuid.uuid4(), company_id=company_id or uuid.uuid4(), integrity_score=score, status="complete")


async def test_band_crossing_creates_one_alert_per_watcher():
    watcher_a, watcher_b = uuid.uuid4(), uuid.uuid4()
    # 85.0 -> "strong", 55.0 -> "moderate": a real band crossing.
    session = FakeSession([_previous(85.0)], [watcher_a, watcher_b])
    ctx = _ctx(session, analysis_score=55.0)

    await _generate_watchlist_alerts(ctx)

    assert len(session.added) == 2
    assert all(isinstance(a, WatchlistAlert) for a in session.added)
    assert {a.user_id for a in session.added} == {watcher_a, watcher_b}
    for alert in session.added:
        assert alert.previous_score == 85.0
        assert alert.new_score == 55.0
        assert alert.previous_risk == "strong"
        assert alert.new_risk == "moderate"
        assert alert.company_id == ctx.company_id
        assert alert.analysis_id == ctx.analysis_id
    assert session.committed is True


async def test_same_band_creates_no_alert():
    # 85.0 and 82.0 are both "strong" -- no crossing.
    session = FakeSession([_previous(85.0)], [uuid.uuid4()])
    ctx = _ctx(session, analysis_score=82.0)

    await _generate_watchlist_alerts(ctx)

    assert session.added == []
    assert session.committed is False


async def test_no_previous_analysis_creates_no_alert():
    session = FakeSession([], [uuid.uuid4()])  # first call: no prior row
    ctx = _ctx(session, analysis_score=55.0)

    await _generate_watchlist_alerts(ctx)

    assert session.added == []
    assert session.committed is False


async def test_missing_previous_score_is_skipped_not_crashed():
    session = FakeSession([_previous(None)], [uuid.uuid4()])
    ctx = _ctx(session, analysis_score=55.0)

    await _generate_watchlist_alerts(ctx)  # must not raise

    assert session.added == []
    assert session.committed is False


async def test_missing_current_score_is_skipped_not_crashed():
    session = FakeSession([_previous(85.0)], [uuid.uuid4()])
    ctx = _ctx(session, analysis_score=None)

    await _generate_watchlist_alerts(ctx)  # must not raise

    assert session.added == []
    assert session.committed is False


async def test_no_watchers_creates_no_alert_and_no_commit():
    # Band crosses, but nobody is watching this company.
    session = FakeSession([_previous(85.0)], [])
    ctx = _ctx(session, analysis_score=55.0)

    await _generate_watchlist_alerts(ctx)

    assert session.added == []
    assert session.committed is False
