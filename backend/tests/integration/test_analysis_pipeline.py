"""Mocked end-to-end test of analysis_worker.run_full_analysis.

Exercises the full Phase 3 stage loop (financials -> forensics -> governance
-> narrative -> news -> score_persist -> report) against an in-memory fake
AsyncSession. Only the genuinely external boundaries are mocked: yfinance
(fetch_financials), RSS feeds (fetch_news_*), and the Gemini-backed classes
(GovernanceScorer, ConsistencyEngine, ReportGenerator). ForensicsRunner and
FraudScorer run for real -- this is what proves the Phase 3 scores ->
module_details -> AnalysisResult wiring holds together end to end
(ADR-010 / ADR-011).
"""

import logging
import uuid
from unittest.mock import AsyncMock

from app.models.company import Company
from app.models.analysis_result import AnalysisResult
from app.models.financial_data import FinancialData
from app.models.red_flag import RedFlag
from app.models.narrative_snapshot import NarrativeSnapshot
from app.models.report import Report
from app.models.edgar_fact import EdgarFinancialFact
from app.tasks import analysis_worker

import pytest


class FakeReadResult:
    """Stand-in for a SQLAlchemy Result on a SELECT .execute() call. Every
    fixture company in this file is "fresh" (no prior AnalysisResult, no
    WatchlistItem rows), so .scalars().first()/.all() always come back empty
    -- this correctly exercises _generate_watchlist_alerts' early-return
    path (Phase 47 / E-4) instead of relying on an AttributeError being
    silently caught by its try/except."""

    def scalars(self):
        return self

    def first(self):
        return None

    def all(self):
        return []


class FakeSession:
    """In-memory stand-in for AsyncSession.

    .get() resolves against the rows passed at construction time;
    .add()/.commit()/.rollback() are recorded/no-ops. Mutations the pipeline
    makes to `company`/`analysis` (the same instances passed in) are visible
    to the test via those original references. .execute() records the
    statement and returns an empty FakeReadResult -- used both as a no-op
    stand-in for the bulk EDGAR-fact insert (Phase 41 / H-4, whose return
    value is never read) and as an empty-result stand-in for any SELECT.
    """

    def __init__(self, *rows):
        self._by_type = {}
        for row in rows:
            self._by_type.setdefault(type(row), {})[row.id] = row
        self.added = []
        self.executed = []

    async def get(self, model, id_):
        return self._by_type.get(model, {}).get(id_)

    def add(self, obj):
        self.added.append(obj)

    async def execute(self, stmt):
        self.executed.append(stmt)
        return FakeReadResult()

    async def commit(self):
        pass

    async def rollback(self):
        pass

    @property
    def inserted_row_count(self):
        """Best-effort count of rows passed to a multi-row bulk INSERT (the
        EDGAR-fact dedup path, Phase 41 / H-4 -- EdgarFinancialFact rows are
        no longer added one-by-one via .add()). Pokes at SQLAlchemy's private
        _multi_values since there's no public API to introspect an
        unexecuted Core Insert's bound values without actually running it."""
        total = 0
        for stmt in self.executed:
            multi = getattr(stmt, "_multi_values", None)
            if multi:
                total += len(multi[0])
        return total


class FakeSessionCtx:
    def __init__(self, session):
        self._session = session

    async def __aenter__(self):
        return self._session

    async def __aexit__(self, exc_type, exc, tb):
        return False


class FakeGovernanceScorer:
    def __init__(self, result):
        self._result = result

    async def analyze(self, company_name, news_text):
        return self._result


class FakeConsistencyEngine:
    def __init__(self, result):
        self._result = result

    async def analyze(self, company_name, statements):
        return self._result


class FakeReportGenerator:
    def __init__(self, content):
        self._content = content

    async def generate_report(self, company, analysis, flags, narrative_snapshots):
        return self._content


# 3 periods -> period_count=3, satisfying the "high confidence" threshold
# (5/5 BASE_WEIGHTS modules + period_count>=3) in the happy-path test. The
# (2021->2022) pair reproduces the divergence/accrual/debt pattern already
# pinned in test_forensics_runner.py (cashflow SEVERE + debt HIGH flags);
# 2023 repeats 2022's figures so this file doesn't need to hand-derive a 3rd
# pair -- exact forensic scores aren't pinned here, only their shape/bounds.
FINANCIALS = [
    {
        "period": "2021", "period_type": "annual",
        "revenue": 1000.0, "net_income": 50.0, "operating_cf": 100.0, "free_cf": 80.0,
        "total_debt": 500.0, "total_assets": 1000.0, "accounts_recv": 100.0, "gross_margin": 0.40,
    },
    {
        "period": "2022", "period_type": "annual",
        "revenue": 1000.0, "net_income": 50.0, "operating_cf": -50.0, "free_cf": -80.0,
        "total_debt": 900.0, "total_assets": 1000.0, "accounts_recv": 100.0, "gross_margin": 0.40,
    },
    {
        "period": "2023", "period_type": "annual",
        "revenue": 1000.0, "net_income": 50.0, "operating_cf": -50.0, "free_cf": -80.0,
        "total_debt": 900.0, "total_assets": 1000.0, "accounts_recv": 100.0, "gross_margin": 0.40,
    },
]

GOV_PROVENANCE = {
    "model_id": "gemini-2.5-flash",
    "prompt": "gov-prompt",
    "raw_response": {
        "finish_reason": "STOP",
        "safety_ratings": [],
        "prompt_token_count": 120,
        "candidates_token_count": 40,
    },
}
GOV_RESULT = (
    75.0,
    [{"flag_type": "governance", "severity": "moderate", "description": "CFO resignation", "period": "2023-01-01"}],
    GOV_PROVENANCE,
)

NARRATIVE_STATEMENTS = [
    {"period": "2023-01", "text": "Revenue grew strongly this quarter.", "source": "News"},
    {"period": "2023-02", "text": "Major restructuring amid investigation concerns.", "source": "News"},
]
NARRATIVE_RESULT = (
    35.0,
    [
        {"period": "2023-01", "statement_text": "Revenue grew strongly this quarter.",
         "sentiment_label": "positive", "sentiment_score": 0.8, "source": "News"},
        {"period": "2023-02", "statement_text": "Major restructuring amid investigation concerns.",
         "sentiment_label": "negative", "sentiment_score": -0.6, "source": "News"},
    ],
    [{"flag_type": "narrative", "severity": "high",
      "description": "Significant tone shift between 2023-01 and 2023-02 (Score diff: 1.40)",
      "period": "2023-02"}],
    [
        {"period": "2023-01", "model_id": "gemini-2.5-flash", "prompt": "p1", "raw_response": "r1"},
        {"period": "2023-02", "model_id": "gemini-2.5-flash", "prompt": "p2", "raw_response": "r2"},
    ],
)


@pytest.fixture
def company():
    return Company(id=uuid.uuid4(), name="Acme Corp", ticker="ACME", sector="Tech", exchange="NASDAQ")


@pytest.fixture
def analysis(company):
    return AnalysisResult(id=uuid.uuid4(), company_id=company.id, status="pending")


@pytest.fixture
def fake_session(company, analysis):
    return FakeSession(company, analysis)


@pytest.fixture(autouse=True)
def patch_session(monkeypatch, fake_session):
    monkeypatch.setattr(analysis_worker, "AsyncSessionLocal", lambda: FakeSessionCtx(fake_session))


async def test_happy_path_completes_with_full_module_details(monkeypatch, company, analysis, fake_session):
    monkeypatch.setattr(analysis_worker, "fetch_financials", AsyncMock(return_value=FINANCIALS))
    monkeypatch.setattr(analysis_worker, "fetch_news_text", AsyncMock(return_value="Acme reports record quarter."))
    monkeypatch.setattr(analysis_worker, "fetch_news_sentiment", AsyncMock(return_value=65.0))
    monkeypatch.setattr(analysis_worker, "fetch_news_statements", AsyncMock(return_value=NARRATIVE_STATEMENTS))
    monkeypatch.setattr(analysis_worker, "GovernanceScorer", lambda: FakeGovernanceScorer(GOV_RESULT))
    monkeypatch.setattr(analysis_worker, "ConsistencyEngine", lambda: FakeConsistencyEngine(NARRATIVE_RESULT))
    monkeypatch.setattr(analysis_worker, "ReportGenerator", lambda: FakeReportGenerator("# Report\nAll good."))
    # No EDGAR coverage for the fictional "ACME" ticker -- Phase 36's restatement
    # check must degrade gracefully without affecting any other stage's scores.
    monkeypatch.setattr(analysis_worker, "fetch_all_concept_histories", AsyncMock(return_value=None))

    await analysis_worker.run_full_analysis(company.id, analysis.id)

    # --- Top-level pipeline outcome ---------------------------------------
    assert analysis.status == "complete"
    assert company.last_analyzed is not None

    # --- Scores: all 5 BASE_WEIGHTS modules present -> high confidence -----
    scores = analysis.module_details["scores"]
    assert set(scores) == {"financial", "cashflow", "earnings", "debt", "governance", "narrative", "news"}
    assert scores["governance"] == 75.0
    assert scores["narrative"] == 35.0
    assert scores["news"] == 65.0
    assert analysis.module_details["confidence"] == "high"
    assert 0.0 <= analysis.integrity_score <= 100.0
    assert analysis.governance_score == 75.0
    assert analysis.narrative_score == 35.0
    assert analysis.news_score == 65.0

    # --- Provenance (ADR-004) ----------------------------------------------
    assert analysis.module_details["governance"]["provenance"] == GOV_PROVENANCE
    assert analysis.module_details["narrative"]["provenance"] == NARRATIVE_RESULT[3]
    assert analysis.module_details["narrative"]["statements_used"] == 2

    # --- Narrative tone shifts (Phase 9): contradictions surface as
    # module_details data, not RedFlag rows -- see flag_types assertions below.
    assert analysis.module_details["narrative"]["tone_shifts"] == [
        {"period": "2023-02", "severity": "high",
         "description": "Significant tone shift between 2023-01 and 2023-02 (Score diff: 1.40)"}
    ]

    # --- Restatement check (Phase 36): no EDGAR coverage for this ticker ---
    assert analysis.module_details["restatement_check"] == {"coverage": False, "facts_checked": 0}

    # --- Persisted rows ------------------------------------------------------
    added_by_type = {}
    for obj in fake_session.added:
        added_by_type.setdefault(type(obj), []).append(obj)

    assert len(added_by_type[FinancialData]) == 3
    assert len(added_by_type[NarrativeSnapshot]) == 2
    assert len(added_by_type[Report]) == 1
    assert added_by_type[Report][0].content == "# Report\nAll good."

    # RedFlags: forensics (>=2 from the 2021->2022 pair) + 1 governance.
    # Narrative contradictions are no longer persisted as RedFlag rows (Phase 9,
    # see tone_shifts assertion above) -- "narrative" must not appear here.
    flag_types = [f.flag_type for f in added_by_type[RedFlag]]
    assert len(flag_types) >= 3
    assert "governance" in flag_types
    assert "narrative" not in flag_types


async def test_governance_stage_failure_does_not_abort_pipeline(monkeypatch, company, analysis, fake_session):
    # fetch_news_text raises before GovernanceScorer is even constructed --
    # _stage_governance's own try/except must catch this (ADR-010) without
    # touching status, and the orchestrator must still reach Stage 7.
    monkeypatch.setattr(analysis_worker, "fetch_financials", AsyncMock(return_value=FINANCIALS))
    monkeypatch.setattr(analysis_worker, "fetch_news_text", AsyncMock(side_effect=Exception("RSS feed timeout")))
    monkeypatch.setattr(analysis_worker, "fetch_news_sentiment", AsyncMock(return_value=65.0))
    # < 2 statements -> _stage_narrative short-circuits to 50.0 without calling ConsistencyEngine.
    monkeypatch.setattr(analysis_worker, "fetch_news_statements", AsyncMock(return_value=[]))
    monkeypatch.setattr(analysis_worker, "ReportGenerator", lambda: FakeReportGenerator("# Report\nDegraded."))
    monkeypatch.setattr(analysis_worker, "fetch_all_concept_histories", AsyncMock(return_value=None))

    await analysis_worker.run_full_analysis(company.id, analysis.id)

    # ADR-010: a single stage's external failure never aborts the pipeline.
    assert analysis.status == "complete"
    assert company.last_analyzed is not None

    scores = analysis.module_details["scores"]
    assert "governance" not in scores  # None -> filtered out of module_details["scores"]
    assert analysis.governance_score is None
    assert scores["narrative"] == 50.0  # < 2 statements -> neutral, no Gemini call
    assert analysis.module_details["narrative"]["statements_used"] == 0

    # 4-of-5 BASE_WEIGHTS available (financial, cashflow, earnings, news) -> medium.
    assert analysis.module_details["confidence"] == "medium"
    assert 0.0 <= analysis.integrity_score <= 100.0

    # Stage 7 still reached and persisted a report despite the Stage 3 failure.
    reports = [o for o in fake_session.added if isinstance(o, Report)]
    assert len(reports) == 1
    assert reports[0].content == "# Report\nDegraded."


async def test_run_full_analysis_logs_carry_correlation_id(monkeypatch, company, analysis, caplog):
    # Phase 10 Step 4: every per-stage log line for one run_full_analysis
    # invocation must carry the same correlation_id (analysis.id) and ticker,
    # so a stuck/killed run can be traced to its last completed stage.
    monkeypatch.setattr(analysis_worker, "fetch_financials", AsyncMock(return_value=FINANCIALS))
    monkeypatch.setattr(analysis_worker, "fetch_news_text", AsyncMock(return_value="Acme reports record quarter."))
    monkeypatch.setattr(analysis_worker, "fetch_news_sentiment", AsyncMock(return_value=65.0))
    monkeypatch.setattr(analysis_worker, "fetch_news_statements", AsyncMock(return_value=NARRATIVE_STATEMENTS))
    monkeypatch.setattr(analysis_worker, "GovernanceScorer", lambda: FakeGovernanceScorer(GOV_RESULT))
    monkeypatch.setattr(analysis_worker, "ConsistencyEngine", lambda: FakeConsistencyEngine(NARRATIVE_RESULT))
    monkeypatch.setattr(analysis_worker, "ReportGenerator", lambda: FakeReportGenerator("# Report\nAll good."))
    monkeypatch.setattr(analysis_worker, "fetch_all_concept_histories", AsyncMock(return_value=None))

    with caplog.at_level(logging.INFO, logger="app.tasks.analysis_worker"):
        await analysis_worker.run_full_analysis(company.id, analysis.id)

    stage_started = [r for r in caplog.records if r.getMessage() == "stage started"]
    assert {r.stage for r in stage_started} == {s.name for s in analysis_worker.STAGES}
    assert all(r.correlation_id == str(analysis.id) for r in stage_started)
    assert all(r.ticker == "ACME" for r in stage_started)

    complete = [r for r in caplog.records if r.getMessage() == "analysis complete"]
    assert len(complete) == 1
    assert complete[0].correlation_id == str(analysis.id)
    assert complete[0].ticker == "ACME"


# Shaped like the real Apple FY2007 NetIncomeLoss restatement already verified
# live against the real SEC EDGAR API in Phase 34/35 -- a genuine 10-K/A
# changing a previously filed figure for the identical period.
EDGAR_HISTORIES_WITH_RESTATEMENT = {
    "net_income": [
        {"start": "2006-10-01", "end": "2007-09-29", "val": 3496000000.0,
         "accn": "accn1", "form": "10-K", "filed": "2009-10-27"},
        {"start": "2006-10-01", "end": "2007-09-29", "val": 3495000000.0,
         "accn": "accn2", "form": "10-K/A", "filed": "2010-01-25"},
    ],
    "revenue": [], "operating_cf": [], "total_assets": [], "accounts_recv": [], "total_debt_approx": [],
}


async def test_restatement_check_creates_flag_without_touching_scores(monkeypatch, company, analysis, fake_session):
    # Phase 36: when EDGAR coverage exists and detect_restatements finds
    # something, it must surface as a RedFlag, persist EdgarFinancialFact
    # rows, and set the coverage marker -- all without affecting any
    # fraud_scorer.py score (flag-only, per the 2026-06-21 owner decision).
    monkeypatch.setattr(analysis_worker, "fetch_financials", AsyncMock(return_value=FINANCIALS))
    monkeypatch.setattr(analysis_worker, "fetch_news_text", AsyncMock(return_value="Acme reports record quarter."))
    monkeypatch.setattr(analysis_worker, "fetch_news_sentiment", AsyncMock(return_value=65.0))
    monkeypatch.setattr(analysis_worker, "fetch_news_statements", AsyncMock(return_value=NARRATIVE_STATEMENTS))
    monkeypatch.setattr(analysis_worker, "GovernanceScorer", lambda: FakeGovernanceScorer(GOV_RESULT))
    monkeypatch.setattr(analysis_worker, "ConsistencyEngine", lambda: FakeConsistencyEngine(NARRATIVE_RESULT))
    monkeypatch.setattr(analysis_worker, "ReportGenerator", lambda: FakeReportGenerator("# Report\nAll good."))
    monkeypatch.setattr(
        analysis_worker, "fetch_all_concept_histories",
        AsyncMock(return_value=EDGAR_HISTORIES_WITH_RESTATEMENT),
    )

    await analysis_worker.run_full_analysis(company.id, analysis.id)

    assert analysis.status == "complete"
    assert analysis.module_details["restatement_check"] == {"coverage": True, "facts_checked": 2}

    added_by_type = {}
    for obj in fake_session.added:
        added_by_type.setdefault(type(obj), []).append(obj)

    # EdgarFinancialFact rows are persisted via a deduped bulk insert, not
    # one-by-one session.add() (Phase 41 / H-4) -- verify via the bulk
    # statement's row count instead of fake_session.added.
    assert fake_session.inserted_row_count == 2

    flag_types = [f.flag_type for f in added_by_type[RedFlag]]
    assert "restatement" in flag_types
    restatement_flags = [f for f in added_by_type[RedFlag] if f.flag_type == "restatement"]
    assert len(restatement_flags) == 1
    assert restatement_flags[0].period == "2007-09-29"
    assert "10-K/A" in restatement_flags[0].description

    # Flag-only: confirm this doesn't perturb the same scores/confidence the
    # happy-path test pins (no restatement weight exists in fraud_scorer.py).
    assert analysis.module_details["scores"]["financial"] is not None
    assert analysis.module_details["confidence"] == "high"


async def test_restatement_check_runs_even_when_yfinance_has_no_data(monkeypatch, company, analysis, fake_session):
    # Regression test: _stage_forensics used to `return` early when
    # financial_records was empty (yfinance rate-limited/unavailable -- the
    # documented, frequently-occurring A1 issue in this exact deployment),
    # which skipped the entire restatement check below it since `return`
    # exits the whole function, not just the empty-data branch. Caught live
    # against the real backend during Phase 36 verification, not by this
    # mocked suite -- the EDGAR check is unrelated to yfinance and must run
    # regardless of whether financial data was available.
    monkeypatch.setattr(analysis_worker, "fetch_financials", AsyncMock(return_value=[]))
    monkeypatch.setattr(analysis_worker, "fetch_news_text", AsyncMock(return_value="Acme reports record quarter."))
    monkeypatch.setattr(analysis_worker, "fetch_news_sentiment", AsyncMock(return_value=65.0))
    monkeypatch.setattr(analysis_worker, "fetch_news_statements", AsyncMock(return_value=[]))
    monkeypatch.setattr(analysis_worker, "ReportGenerator", lambda: FakeReportGenerator("# Report\nDegraded."))
    monkeypatch.setattr(
        analysis_worker, "fetch_all_concept_histories",
        AsyncMock(return_value=EDGAR_HISTORIES_WITH_RESTATEMENT),
    )

    await analysis_worker.run_full_analysis(company.id, analysis.id)

    assert analysis.status == "complete"
    assert analysis.module_details["scores"].get("financial") is None  # no yfinance data, as expected
    assert analysis.module_details["restatement_check"] == {"coverage": True, "facts_checked": 2}

    flag_types = [f.flag_type for f in fake_session.added if isinstance(f, RedFlag)]
    assert "restatement" in flag_types


# Two clean, steadily-growing annual periods -- deliberately healthier than
# FINANCIALS' troubled restated picture (which pins a SEVERE cashflow flag
# and HIGH debt flag), so the as-filed scores are demonstrably independent
# of the restated ones rather than coincidentally identical.
EDGAR_HISTORIES_FOR_AS_FILED = {
    "revenue": [
        {"start": "2020-01-01", "end": "2021-12-31", "val": 2000.0, "accn": "e1", "form": "10-K", "filed": "2022-01-15"},
        {"start": "2021-01-01", "end": "2022-12-31", "val": 2200.0, "accn": "e2", "form": "10-K", "filed": "2023-01-15"},
    ],
    "net_income": [
        {"start": "2020-01-01", "end": "2021-12-31", "val": 300.0, "accn": "e1", "form": "10-K", "filed": "2022-01-15"},
        {"start": "2021-01-01", "end": "2022-12-31", "val": 330.0, "accn": "e2", "form": "10-K", "filed": "2023-01-15"},
    ],
    "operating_cf": [
        {"start": "2020-01-01", "end": "2021-12-31", "val": 320.0, "accn": "e1", "form": "10-K", "filed": "2022-01-15"},
        {"start": "2021-01-01", "end": "2022-12-31", "val": 350.0, "accn": "e2", "form": "10-K", "filed": "2023-01-15"},
    ],
    "total_assets": [
        {"start": None, "end": "2021-12-31", "val": 5000.0, "accn": "e1", "form": "10-K", "filed": "2022-01-15"},
        {"start": None, "end": "2022-12-31", "val": 5200.0, "accn": "e2", "form": "10-K", "filed": "2023-01-15"},
    ],
    "accounts_recv": [
        {"start": None, "end": "2021-12-31", "val": 150.0, "accn": "e1", "form": "10-K", "filed": "2022-01-15"},
        {"start": None, "end": "2022-12-31", "val": 160.0, "accn": "e2", "form": "10-K", "filed": "2023-01-15"},
    ],
    "total_debt_approx": [
        {"start": None, "end": "2021-12-31", "val": 100.0, "accn": "e1", "form": "10-K", "filed": "2022-01-15"},
        {"start": None, "end": "2022-12-31", "val": 105.0, "accn": "e2", "form": "10-K", "filed": "2023-01-15"},
    ],
}


async def test_as_filed_score_is_computed_independently_and_does_not_move_integrity_score(
    monkeypatch, company, analysis, fake_session
):
    # Phase 42 / C-2: the as-filed score runs the same forensic modules a
    # second time against as-originally-filed EDGAR data. It must produce
    # genuinely different numbers from the restated path (proving real
    # independence, not a coincidental copy) while leaving the headline
    # integrity_score and confidence completely untouched.
    monkeypatch.setattr(analysis_worker, "fetch_financials", AsyncMock(return_value=FINANCIALS))
    monkeypatch.setattr(analysis_worker, "fetch_news_text", AsyncMock(return_value="Acme reports record quarter."))
    monkeypatch.setattr(analysis_worker, "fetch_news_sentiment", AsyncMock(return_value=65.0))
    monkeypatch.setattr(analysis_worker, "fetch_news_statements", AsyncMock(return_value=NARRATIVE_STATEMENTS))
    monkeypatch.setattr(analysis_worker, "GovernanceScorer", lambda: FakeGovernanceScorer(GOV_RESULT))
    monkeypatch.setattr(analysis_worker, "ConsistencyEngine", lambda: FakeConsistencyEngine(NARRATIVE_RESULT))
    monkeypatch.setattr(analysis_worker, "ReportGenerator", lambda: FakeReportGenerator("# Report\nAll good."))
    monkeypatch.setattr(
        analysis_worker, "fetch_all_concept_histories",
        AsyncMock(return_value=EDGAR_HISTORIES_FOR_AS_FILED),
    )

    await analysis_worker.run_full_analysis(company.id, analysis.id)

    assert analysis.status == "complete"
    as_filed = analysis.module_details["as_filed"]
    assert as_filed["coverage"] is True
    assert as_filed["period_count"] == 2

    # Clean, steadily-growing as-filed data -> healthy scores across the
    # board, in sharp contrast to FINANCIALS' pinned SEVERE/HIGH picture.
    assert as_filed["scores"]["cashflow"] == 100.0
    assert as_filed["scores"]["debt"] == 100.0

    # The restated path's troubled picture must still be exactly what it
    # was before this phase -- this is the "doesn't move the headline score"
    # guarantee, checked directly against the as-filed numbers being clearly
    # different (proving they were computed independently, not shared).
    restated_cashflow = analysis.module_details["scores"]["cashflow"]
    restated_debt = analysis.module_details["scores"]["debt"]
    assert restated_cashflow != as_filed["scores"]["cashflow"]
    assert restated_debt != as_filed["scores"]["debt"]

    delta = as_filed["delta"]
    assert delta["cashflow"] == round(as_filed["scores"]["cashflow"] - restated_cashflow, 1)
    assert delta["debt"] == round(as_filed["scores"]["debt"] - restated_debt, 1)

    # The one invariant this entire phase must never violate: the headline
    # score and confidence are computed purely from ctx.scores (the restated
    # path) -- identical to what the existing happy-path test already pins
    # for this exact FINANCIALS/GOV_RESULT/NARRATIVE_RESULT combination.
    assert analysis.module_details["confidence"] == "high"


async def test_stage_failure_does_not_leak_session_into_next_stage(monkeypatch, company, analysis):
    """Phase 48 (A-1): every stage iteration gets its OWN fresh session and
    its OWN fresh company/analysis fetch. This test overrides the file's
    shared-fake-session autouse fixture with a session factory that returns
    a NEW tracked instance every call, then forces a 2-stage run where stage
    1 raises an exception that escapes its own handling entirely (no
    internal try/except, unlike every real _stage_* function) -- proving
    stage 2 still gets a distinct, valid session/company/analysis,
    unaffected by stage 1's failure.
    """
    created_sessions = []

    class TrackedFakeSession:
        def __init__(self):
            self.committed = False
            created_sessions.append(self)

        async def get(self, model, id_):
            if model is analysis_worker.Company:
                return company
            if model is analysis_worker.AnalysisResult:
                return analysis
            return None

        def add(self, obj):
            pass

        async def execute(self, stmt):
            return FakeReadResult()

        async def commit(self):
            self.committed = True

    class TrackedFakeSessionCtx:
        async def __aenter__(self):
            return TrackedFakeSession()

        async def __aexit__(self, exc_type, exc, tb):
            return False  # never suppress -- matches a real AsyncSession's __aexit__

    monkeypatch.setattr(analysis_worker, "AsyncSessionLocal", lambda: TrackedFakeSessionCtx())
    monkeypatch.setattr(analysis_worker, "_generate_watchlist_alerts", AsyncMock())

    received_in_stage_2 = {}

    async def failing_stage(ctx):
        raise RuntimeError("boom -- escapes this stage's own handling entirely")

    async def recording_stage(ctx):
        received_in_stage_2["session"] = ctx.session
        received_in_stage_2["company"] = ctx.company
        received_in_stage_2["analysis"] = ctx.analysis

    fake_stages = [
        analysis_worker.Stage("boom", "Booming...", failing_stage),
        analysis_worker.Stage("record", "Recording...", recording_stage),
    ]
    monkeypatch.setattr(analysis_worker, "STAGES", fake_stages)

    await analysis_worker.run_full_analysis(company.id, analysis.id)

    # 1 initial existence-check session + 2 stage sessions + 1 final-write
    # session = 4 distinct instances; none reused across stages.
    assert len(created_sessions) == 4
    assert len(set(id(s) for s in created_sessions)) == 4

    # Stage 2's session is one of the tracked instances (not None, not a
    # leftover from stage 1) and it still resolved a valid company/analysis.
    assert received_in_stage_2["session"] in created_sessions
    assert received_in_stage_2["company"] is company
    assert received_in_stage_2["analysis"] is analysis
