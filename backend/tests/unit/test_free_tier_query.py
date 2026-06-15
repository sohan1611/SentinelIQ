"""Free-tier metering rewrite (ADR-007 / Decision #1 / defect C-4): AnalysisRun is the
user-scoped audit/metering log, counted by user_id + calendar month. Regression guard
against the old broken AnalysisResult<->WatchlistItem join (C-4), which both
under- and over-counted usage.
"""

import uuid
from datetime import datetime, timedelta

from app.api.v1.routes.analysis import (
    _free_tier_usage_query,
    ANALYSIS_CACHE_TTL,
    FREE_TIER_MONTHLY_LIMIT,
)


def test_free_tier_monthly_limit_matches_claude_md():
    # CLAUDE.md decision #14 / Error Handling rule 5: 5 analyses per calendar month.
    assert FREE_TIER_MONTHLY_LIMIT == 5


def test_analysis_cache_ttl_matches_claude_md():
    # CLAUDE.md caching strategy: "company:{ticker}:analysis" -> 6 hours.
    assert ANALYSIS_CACHE_TTL == timedelta(hours=6)


def test_free_tier_usage_query_counts_analysis_runs_by_user_and_month():
    user_id = uuid.uuid4()
    since = datetime(2026, 6, 1)
    sql = str(_free_tier_usage_query(user_id, since))

    assert "analysis_runs" in sql
    assert "analysis_runs.user_id" in sql
    assert "analysis_runs.run_at" in sql

    # C-4 regression guard: the old query joined AnalysisResult -> WatchlistItem,
    # which both under- and over-counted usage. Neither table should appear here.
    assert "watchlist" not in sql
    assert "analysis_results" not in sql
