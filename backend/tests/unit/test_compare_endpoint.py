"""GET /analysis/compare (Phase 37, F5 scoped to a comparison view): each
requested ticker's latest completed analysis, side by side. Read-only over
data that already exists -- no scoring changes, no new tables.
"""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from app.api.v1.routes.analysis import compare_analyses, COMPARE_MAX_TICKERS
from app.models.company import Company
from app.models.analysis_result import AnalysisResult
from app.models.user import User


def _execute_result(value, *, first=False):
    result = MagicMock()
    if first:
        result.scalars.return_value.first.return_value = value
    else:
        result.scalars.return_value.all.return_value = value
    return result


def _scalar_result(value):
    result = MagicMock()
    result.scalar.return_value = value
    return result


@pytest.fixture
def aapl():
    return Company(id=uuid.uuid4(), name="Apple Inc.", ticker="AAPL", sector="Tech", exchange="NASDAQ")


@pytest.fixture
def msft():
    return Company(id=uuid.uuid4(), name="Microsoft Corp.", ticker="MSFT", sector="Tech", exchange="NASDAQ")


@pytest.fixture
def current_user():
    return User(id=uuid.uuid4(), email="test@example.com", hashed_pw="x")


async def test_two_companies_both_analyzed(aapl, msft, current_user):
    now = datetime.now(timezone.utc)
    aapl_analysis = AnalysisResult(id=uuid.uuid4(), company_id=aapl.id, run_at=now, status="complete", integrity_score=72.0)
    msft_analysis = AnalysisResult(id=uuid.uuid4(), company_id=msft.id, run_at=now, status="complete", integrity_score=88.0)

    db = AsyncMock()
    db.execute = AsyncMock(side_effect=[
        _execute_result(aapl, first=True),
        _execute_result(aapl_analysis, first=True),
        _scalar_result(2),
        _execute_result(msft, first=True),
        _execute_result(msft_analysis, first=True),
        _scalar_result(0),
    ])

    result = await compare_analyses("AAPL,MSFT", db=db, current_user=current_user)

    assert len(result) == 2
    assert result[0].ticker == "AAPL"
    assert result[0].found is True
    assert result[0].analysis.integrity_score == 72.0
    assert result[0].red_flag_count == 2
    assert result[1].ticker == "MSFT"
    assert result[1].analysis.integrity_score == 88.0
    assert result[1].red_flag_count == 0


async def test_unknown_ticker_marked_not_found_without_querying_analysis(current_user):
    db = AsyncMock()
    db.execute = AsyncMock(side_effect=[
        _execute_result(None, first=True),  # ZZZZ: no company row
        _execute_result(None, first=True),  # QQQQ: no company row
    ])

    result = await compare_analyses("ZZZZ,QQQQ", db=db, current_user=current_user)

    assert result[0].ticker == "ZZZZ"
    assert result[0].found is False
    assert result[0].analysis is None
    assert result[1].ticker == "QQQQ"
    assert result[1].found is False
    # Only 2 db.execute calls for 2 tickers -- a missing company short-circuits
    # before a second (analysis) query is ever issued for it.
    assert db.execute.await_count == 2


async def test_known_company_with_no_completed_analysis(aapl, current_user):
    db = AsyncMock()
    db.execute = AsyncMock(side_effect=[
        _execute_result(aapl, first=True),
        _execute_result(None, first=True),  # no completed AnalysisResult yet
        _execute_result(aapl, first=True),
        _execute_result(None, first=True),
    ])

    result = await compare_analyses("AAPL,AAPL", db=db, current_user=current_user)

    assert result[0].found is True
    assert result[0].company_name == "Apple Inc."
    assert result[0].analysis is None  # distinct from found=False -- a real company, just not analyzed


async def test_rejects_fewer_than_two_tickers(current_user):
    db = AsyncMock()

    with pytest.raises(HTTPException) as exc_info:
        await compare_analyses("AAPL", db=db, current_user=current_user)

    assert exc_info.value.status_code == 400


async def test_rejects_more_than_max_tickers(current_user):
    db = AsyncMock()
    too_many = ",".join(f"T{i}" for i in range(COMPARE_MAX_TICKERS + 1))

    with pytest.raises(HTTPException) as exc_info:
        await compare_analyses(too_many, db=db, current_user=current_user)

    assert exc_info.value.status_code == 400


async def test_tickers_are_normalized_to_uppercase_and_trimmed(aapl, current_user):
    db = AsyncMock()
    db.execute = AsyncMock(side_effect=[
        _execute_result(aapl, first=True),
        _execute_result(None, first=True),
        _execute_result(aapl, first=True),
        _execute_result(None, first=True),
    ])

    result = await compare_analyses(" aapl , AAPL ", db=db, current_user=current_user)

    assert result[0].ticker == "AAPL"
    assert result[1].ticker == "AAPL"
