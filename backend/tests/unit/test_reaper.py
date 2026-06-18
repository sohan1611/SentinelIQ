"""Stuck-analysis reaper (Phase 10 Step 3, OPUS_ARCHITECTURAL_REVIEW.md Sec.8 item 3 /
ADR-012): a Render free-tier spin-down/restart can kill the in-process background
task mid-analysis, leaving an AnalysisResult frozen at running:<stage> forever. The
reaper marks such rows with the new terminal "error" status -- it must NOT revive the
retired "failed" status (ADR-010 / Phase 3).
"""

import uuid
from datetime import datetime, timedelta, timezone

from app.models.analysis_result import AnalysisResult
from app.tasks.reaper import _stuck_analyses_query, reap_stuck_analyses


class FakeResult:
    def __init__(self, rows):
        self._rows = rows

    def scalars(self):
        return self

    def all(self):
        return self._rows


class FakeSession:
    def __init__(self, rows):
        self._rows = rows
        self.committed = False

    async def execute(self, query):
        return FakeResult(self._rows)

    async def commit(self):
        self.committed = True


def test_stuck_analyses_query_targets_running_status_past_cutoff():
    cutoff = datetime(2026, 6, 16, 12, 0, 0)
    sql = str(_stuck_analyses_query(cutoff))

    assert "analysis_results.status" in sql
    assert "analysis_results.run_at" in sql
    assert "LIKE" in sql.upper()


async def test_reap_stuck_analyses_marks_stale_running_rows_as_error():
    stale = AnalysisResult(
        id=uuid.uuid4(),
        company_id=uuid.uuid4(),
        status="running:forensics",
        run_at=datetime.now(timezone.utc) - timedelta(minutes=30),
    )
    session = FakeSession([stale])

    count = await reap_stuck_analyses(session)

    assert count == 1
    assert stale.status == "error"
    assert session.committed is True


async def test_reap_stuck_analyses_is_noop_when_nothing_stuck():
    session = FakeSession([])

    count = await reap_stuck_analyses(session)

    assert count == 0
    assert session.committed is False
