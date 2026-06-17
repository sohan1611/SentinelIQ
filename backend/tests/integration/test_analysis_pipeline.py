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
from app.tasks import analysis_worker

import pytest


class FakeSession:
    """In-memory stand-in for AsyncSession.

    .get() resolves against the rows passed at construction time;
    .add()/.commit()/.rollback() are recorded/no-ops. Mutations the pipeline
    makes to `company`/`analysis` (the same instances passed in) are visible
    to the test via those original references.
    """

    def __init__(self, *rows):
        self._by_type = {}
        for row in rows:
            self._by_type.setdefault(type(row), {})[row.id] = row
        self.added = []

    async def get(self, model, id_):
        return self._by_type.get(model, {}).get(id_)

    def add(self, obj):
        self.added.append(obj)

    async def commit(self):
        pass

    async def rollback(self):
        pass


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
    "model_id": "gemini-1.5-flash",
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
        {"period": "2023-01", "model_id": "gemini-1.5-flash", "prompt": "p1", "raw_response": "r1"},
        {"period": "2023-02", "model_id": "gemini-1.5-flash", "prompt": "p2", "raw_response": "r2"},
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
