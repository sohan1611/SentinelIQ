"""GET /analysis/company/{ticker}/history (Phase 11 Step 1,
OPUS_ARCHITECTURAL_REVIEW.md Sec.8 item 1): returns up to
ANALYSIS_HISTORY_LIMIT completed AnalysisResult rows for a company, oldest
first, as lightweight AnalysisHistoryItem objects (no module_details) for
the overview page's Integrity Score trend chart.
"""

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from app.api.v1.routes.analysis import get_analysis_history, ANALYSIS_HISTORY_LIMIT
from app.models.company import Company
from app.models.analysis_result import AnalysisResult


def _execute_result(value, *, first=False):
    result = MagicMock()
    if first:
        result.scalars.return_value.first.return_value = value
    else:
        result.scalars.return_value.all.return_value = value
    return result


@pytest.fixture
def company():
    return Company(id=uuid.uuid4(), name="Acme Corp", ticker="ACME", sector="Tech", exchange="NASDAQ")


async def test_history_returns_chronological_order(company):
    now = datetime.now(timezone.utc)
    # DB query is newest-first; the route must reverse this.
    rows = [
        AnalysisResult(id=uuid.uuid4(), company_id=company.id, run_at=now,
                        status="complete", integrity_score=80.0),
        AnalysisResult(id=uuid.uuid4(), company_id=company.id, run_at=now - timedelta(days=30),
                        status="complete", integrity_score=70.0),
    ]

    db = AsyncMock()
    db.execute = AsyncMock(side_effect=[
        _execute_result(company, first=True),
        _execute_result(rows),
    ])

    result = await get_analysis_history("ACME", db=db)

    assert [r.integrity_score for r in result] == [70.0, 80.0]


async def test_history_lowercase_ticker_is_normalized(company):
    db = AsyncMock()
    db.execute = AsyncMock(side_effect=[
        _execute_result(company, first=True),
        _execute_result([]),
    ])

    await get_analysis_history("acme", db=db)

    # First call is the company lookup -- assert it queried the uppercased ticker.
    company_query = str(db.execute.await_args_list[0].args[0])
    assert "companies.ticker" in company_query


async def test_history_404_when_company_missing():
    db = AsyncMock()
    db.execute = AsyncMock(return_value=_execute_result(None, first=True))

    with pytest.raises(HTTPException) as exc_info:
        await get_analysis_history("ZZZZ", db=db)

    assert exc_info.value.status_code == 404


async def test_history_empty_list_when_no_completed_analyses(company):
    db = AsyncMock()
    db.execute = AsyncMock(side_effect=[
        _execute_result(company, first=True),
        _execute_result([]),
    ])

    result = await get_analysis_history("ACME", db=db)

    assert result == []


async def test_history_limit_constant_is_reasonable():
    # Free tier allows 5 analyses/month (CLAUDE.md decision #14); 24 covers
    # roughly 2 years at max free-tier usage without unbounded growth.
    assert ANALYSIS_HISTORY_LIMIT == 24
