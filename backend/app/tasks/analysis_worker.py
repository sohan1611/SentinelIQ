import logging
from dataclasses import dataclass, field
from typing import Awaitable, Callable
from uuid import UUID
from datetime import datetime, timezone

from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.future import select

from app.database import AsyncSessionLocal
from app.models.company import Company
from app.models.analysis_result import AnalysisResult
from app.models.financial_data import FinancialData
from app.models.red_flag import RedFlag
from app.models.narrative_snapshot import NarrativeSnapshot
from app.models.report import Report
from app.models.edgar_fact import EdgarFinancialFact
from app.models.watchlist import WatchlistItem
from app.models.watchlist_alert import WatchlistAlert

from app.services.yahoo_finance import fetch_financials
from app.services.news_aggregator import fetch_news_sentiment, fetch_news_text, fetch_news_statements
from app.services.sec_edgar import fetch_all_concept_histories, fetch_management_statements
from app.services.pipeline_health import record_analysis_outcome
from app.core.forensics.forensics_runner import ForensicsRunner
from app.core.forensics.restatement_detector import detect_restatements
from app.core.forensics.as_filed_adapter import build_as_filed_periods
from app.core.governance.governance_scorer import GovernanceScorer
from app.core.narrative.consistency_engine import ConsistencyEngine
from app.core.scoring.fraud_scorer import FraudScorer
from app.core.ai.report_generator import ReportGenerator
from app.logging_config import CorrelationLoggerAdapter
from app.schemas.analysis import ModuleDetails, CURRENT_SCHEMA_VERSION

logger = logging.getLogger(__name__)

# Three recent 10-K/10-Q filings give three distinct quarters while bounding
# this narrative analysis to three Gemini calls.
NARRATIVE_EDGAR_FILING_LIMIT = 3
# MD&A excerpts are thousands of characters rather than ~100-character
# headlines, and each statement incurs one Gemini call. Truncate at this
# visible cost decision before the engine so source_quote grounding is correct.
NARRATIVE_MAX_STATEMENT_CHARS = 4000


async def update_status(session: AsyncSession, analysis_id: UUID, stage: str):
    analysis = await session.get(AnalysisResult, analysis_id)
    if analysis:
        analysis.status = f"running:{stage}"
        await session.commit()


@dataclass
class StageContext:
    analysis_id: UUID
    company_id: UUID
    log: logging.LoggerAdapter
    # Phase 48 (A-1): reassigned fresh each stage iteration in run_full_analysis's
    # loop, not fixed once for the whole run -- so a stage's rollback can never
    # leave the NEXT stage reading an expired object. None only transiently,
    # before the loop's first iteration sets them.
    session: AsyncSession | None = None
    company: Company | None = None
    analysis: AnalysisResult | None = None
    scores: dict = field(default_factory=dict)
    forensics_details: dict = field(default_factory=dict)
    financial_records: list = field(default_factory=list)
    all_flags: list = field(default_factory=list)
    narrative_snapshots: list = field(default_factory=list)
    narrative_snapshot_data: list = field(default_factory=list)
    narrative_provenance: list = field(default_factory=list)
    narrative_tone_shifts: list = field(default_factory=list)
    narrative_source: str = "none"
    governance_provenance: dict = field(default_factory=dict)
    governance_flags: list = field(default_factory=list)
    financial_data_status: str = "ok"
    edgar_coverage: bool = False
    edgar_facts_checked: int = 0
    as_filed_scores: dict = field(default_factory=dict)
    as_filed_period_count: int = 0


@dataclass
class Stage:
    name: str
    status_text: str
    fn: Callable[[StageContext], Awaitable[None]]


async def _stage_financials(ctx: StageContext):
    try:
        raw_financials = await fetch_financials(ctx.company.ticker)
        for f in raw_financials:
            fd = FinancialData(company_id=ctx.company_id, **f)
            ctx.session.add(fd)
            ctx.financial_records.append(fd)
        await ctx.session.commit()
    except Exception as e:
        status_code = getattr(e, "status_code", None)
        if status_code == 503:
            ctx.financial_data_status = "rate_limited"
            ctx.log.warning(f"Stage financials: Yahoo Finance rate-limited (503)", extra={"stage": "financials"})
        else:
            ctx.financial_data_status = "unavailable"
            ctx.log.error(f"Stage financials failed: {e}", extra={"stage": "financials"})
        await ctx.session.rollback()


async def _stage_forensics(ctx: StageContext):
    try:
        if not ctx.financial_records:
            ctx.scores["financial"] = None
            ctx.scores["cashflow"] = None
            ctx.scores["earnings"] = None
            ctx.scores["debt"] = None
        else:
            forensics_res = ForensicsRunner().run_forensics(ctx.financial_records)
            revenue_score = forensics_res["revenue"].score
            debt_score = forensics_res["debt"].score
            ctx.scores["financial"] = (revenue_score + debt_score) / 2
            ctx.scores["cashflow"] = forensics_res["cashflow"].score
            ctx.scores["earnings"] = forensics_res["earnings"].score
            ctx.scores["debt"] = debt_score

            ctx.forensics_details["revenue"] = forensics_res["revenue"].details
            ctx.forensics_details["cashflow"] = forensics_res["cashflow"].details
            ctx.forensics_details["earnings"] = forensics_res["earnings"].details
            ctx.forensics_details["debt"] = forensics_res["debt"].details

            for f in forensics_res["all_flags"]:
                flag_rec = RedFlag(
                    analysis_id=ctx.analysis_id,
                    company_id=ctx.company_id,
                    flag_type=f.flag_type,
                    severity=f.severity,
                    description=f.description,
                    period=f.period,
                )
                ctx.session.add(flag_rec)
                ctx.all_flags.append(flag_rec)
            await ctx.session.commit()
    except Exception as e:
        ctx.log.error(f"Stage forensics failed: {e}", extra={"stage": "forensics"})
        await ctx.session.rollback()
        ctx.scores["financial"] = None
        ctx.scores["cashflow"] = None
        ctx.scores["earnings"] = None
        ctx.scores["debt"] = None

    # Restatement Detector (Phase 35/36) -- flag-only, no score impact (see
    # MASTER_IMPLEMENTATION_PLAN.md Phase 35 owner decision). Isolated in its
    # own try/except: an EDGAR fetch failure or no-coverage case must never
    # wipe out the yfinance-based forensic scores set above.
    try:
        histories = await fetch_all_concept_histories(ctx.company.ticker)
        if histories:
            ctx.edgar_coverage = True
            facts: list[EdgarFinancialFact] = []
            fact_rows: list[dict] = []
            for concept, entries in histories.items():
                for e in entries:
                    fact_data = {
                        "company_id": ctx.company_id,
                        "concept": concept,
                        "period_start": e.get("start"),
                        "period_end": e["end"],
                        "value": e["val"],
                        "accession_number": e["accn"],
                        "form_type": e["form"],
                        "filed_date": e["filed"],
                    }
                    fact_rows.append(fact_data)
                    # In-memory only, for detect_restatements() below -- the
                    # actual write is the deduped bulk insert further down,
                    # not session.add() (Phase 41 / H-4: re-analyzing an
                    # already-seen company must not duplicate its history).
                    facts.append(EdgarFinancialFact(**fact_data))
            ctx.edgar_facts_checked = len(facts)

            if fact_rows:
                # index_elements, not constraint= -- Postgres's ON CONFLICT ON
                # CONSTRAINT only matches a named table constraint, not a bare
                # CREATE UNIQUE INDEX (confirmed live: constraint= raised
                # UndefinedObjectError against the real DB, something no mock
                # could have caught). index_elements matches by the index's
                # actual column/expression definition instead.
                stmt = pg_insert(EdgarFinancialFact).values(fact_rows).on_conflict_do_nothing(
                    index_elements=[
                        EdgarFinancialFact.company_id,
                        EdgarFinancialFact.concept,
                        func.coalesce(EdgarFinancialFact.period_start, ""),
                        EdgarFinancialFact.period_end,
                        EdgarFinancialFact.accession_number,
                    ]
                )
                await ctx.session.execute(stmt)

            for rf in detect_restatements(facts):
                flag_rec = RedFlag(
                    analysis_id=ctx.analysis_id,
                    company_id=ctx.company_id,
                    flag_type=rf.flag_type,
                    severity=rf.severity,
                    description=rf.description,
                    period=rf.period,
                )
                ctx.session.add(flag_rec)
                ctx.all_flags.append(flag_rec)

            # As-filed forensic score (Phase 42 / C-2) -- runs the existing,
            # unchanged forensic modules a second time against the
            # as-originally-filed EDGAR figures instead of yfinance's
            # restated view. Transient FinancialData objects, never
            # session.add()'d -- this is a parallel in-memory computation,
            # not a second set of rows to persist (same pattern already
            # used for `facts` above). Too few periods degrades via the
            # forensic modules' own existing "zero valid pairs -> 50.0"
            # fallback -- no separate guard needed here.
            as_filed_periods = build_as_filed_periods(histories)
            ctx.as_filed_period_count = len(as_filed_periods)
            as_filed_financial_data = [FinancialData(**p) for p in as_filed_periods]
            as_filed_res = ForensicsRunner().run_forensics(as_filed_financial_data)
            ctx.as_filed_scores["financial"] = (as_filed_res["revenue"].score + as_filed_res["debt"].score) / 2
            ctx.as_filed_scores["cashflow"] = as_filed_res["cashflow"].score
            ctx.as_filed_scores["earnings"] = as_filed_res["earnings"].score
            ctx.as_filed_scores["debt"] = as_filed_res["debt"].score

            await ctx.session.commit()
    except Exception as e:
        ctx.log.error(f"Restatement check failed: {e}", extra={"stage": "forensics"})
        await ctx.session.rollback()
        ctx.edgar_coverage = False
        ctx.edgar_facts_checked = 0
        ctx.as_filed_period_count = 0
        ctx.as_filed_scores = {}


async def _stage_governance(ctx: StageContext):
    try:
        news_text = await fetch_news_text(ctx.company.name, ctx.company.ticker)
        gov_score, gov_flags, provenance = await GovernanceScorer().analyze(ctx.company.name, news_text)
        ctx.scores["governance"] = gov_score
        ctx.governance_provenance = provenance
        ctx.governance_flags = gov_flags
        for gf in gov_flags:
            flag_rec = RedFlag(
                analysis_id=ctx.analysis_id,
                company_id=ctx.company_id,
                flag_type=gf["flag_type"],
                severity=gf["severity"],
                description=gf["description"],
                period=gf.get("period"),
            )
            ctx.session.add(flag_rec)
            ctx.all_flags.append(flag_rec)
        await ctx.session.commit()
    except Exception as e:
        ctx.log.error(f"Stage governance failed: {e}", extra={"stage": "governance"})
        await ctx.session.rollback()
        ctx.scores["governance"] = None


async def _stage_narrative(ctx: StageContext):
    try:
        try:
            statements = await fetch_management_statements(
                ctx.company.ticker, limit=NARRATIVE_EDGAR_FILING_LIMIT
            )
        except Exception as e:
            ctx.log.warning(
                f"EDGAR management statement fetch failed: {e}",
                extra={"stage": "narrative"},
            )
            statements = []

        if len(statements) >= 2:
            narrative_source = "edgar_mdna"
        else:
            statements = await fetch_news_statements(ctx.company.name, ctx.company.ticker, limit=2)
            narrative_source = "news_headlines"

        if len(statements) < 2:
            ctx.narrative_source = "none"
            ctx.scores["narrative"] = 50.0
            return

        statements = [
            {**statement, "text": statement["text"][:NARRATIVE_MAX_STATEMENT_CHARS]}
            for statement in statements
        ]
        ctx.narrative_source = narrative_source
        narrative_score, snaps, cont_flags, provenance = await ConsistencyEngine().analyze(
            ctx.company.name, statements
        )
        ctx.scores["narrative"] = narrative_score
        ctx.narrative_snapshot_data = snaps
        ctx.narrative_provenance = provenance

        for s in snaps:
            sn = NarrativeSnapshot(
                company_id=ctx.company_id,
                fetched_at=datetime.now(timezone.utc).replace(tzinfo=None),
                period=s.get("period"),
                statement_text=s.get("statement_text"),
                sentiment_label=s.get("sentiment_label"),
                sentiment_score=s.get("sentiment_score"),
                source=s.get("source"),
            )
            ctx.session.add(sn)
            ctx.narrative_snapshots.append(sn)

        ctx.narrative_tone_shifts = [
            {"period": cf["period"], "severity": cf["severity"], "description": cf["description"]}
            for cf in cont_flags
        ]

        await ctx.session.commit()
    except Exception as e:
        ctx.log.error(f"Stage narrative failed: {e}", extra={"stage": "narrative"})
        await ctx.session.rollback()
        ctx.scores["narrative"] = 50.0


async def _stage_news(ctx: StageContext):
    try:
        ctx.scores["news"] = await fetch_news_sentiment(ctx.company.name, ctx.company.ticker)
    except Exception as e:
        ctx.log.error(f"Stage news failed: {e}", extra={"stage": "news"})
        ctx.scores["news"] = 50.0


async def _stage_score_persist(ctx: StageContext):
    try:
        period_count = len(ctx.financial_records)
        integrity_score, confidence = FraudScorer().compute_integrity_score(ctx.scores, period_count)

        # As-filed delta (Phase 42 / C-2) -- only computed when both sides
        # are real numbers; if the restated path failed (e.g. yfinance
        # rate-limited), there's nothing meaningful to diff, so that key is
        # omitted, never fabricated as 0. No sign-convention claim is made
        # here (e.g. "positive = fraud") -- that interpretation belongs to
        # the report/UI layer and the analyst, not the backend.
        as_filed_delta = {
            key: round(ctx.as_filed_scores[key] - ctx.scores[key], 1)
            for key in ("financial", "cashflow", "earnings", "debt")
            if key in ctx.as_filed_scores and ctx.scores.get(key) is not None
        }

        ctx.analysis.integrity_score = integrity_score
        ctx.analysis.financial_score = ctx.scores.get("financial")
        ctx.analysis.cashflow_score = ctx.scores.get("cashflow")
        ctx.analysis.governance_score = ctx.scores.get("governance")
        ctx.analysis.earnings_score = ctx.scores.get("earnings")
        ctx.analysis.narrative_score = ctx.scores.get("narrative")
        ctx.analysis.news_score = ctx.scores.get("news")
        ctx.analysis.module_details = ModuleDetails.model_validate({
            "schema_version": CURRENT_SCHEMA_VERSION,
            "scores": {k: v for k, v in ctx.scores.items() if v is not None},
            "confidence": confidence,
            "revenue": ctx.forensics_details.get("revenue", {}),
            "cashflow": ctx.forensics_details.get("cashflow", {}),
            "earnings": ctx.forensics_details.get("earnings", {}),
            "debt": ctx.forensics_details.get("debt", {}),
            "narrative": {
                "snapshots": ctx.narrative_snapshot_data,
                "statements_used": len(ctx.narrative_snapshot_data),
                "provenance": ctx.narrative_provenance,
                "tone_shifts": ctx.narrative_tone_shifts,
                "source": ctx.narrative_source,
            },
            "governance": {
                "provenance": ctx.governance_provenance,
                "low_confidence": ctx.governance_provenance.get("low_confidence", False),
                "flags": ctx.governance_flags,
            },
            "financial_data_status": ctx.financial_data_status if ctx.financial_data_status != "ok" else None,
            "restatement_check": {
                "coverage": ctx.edgar_coverage,
                "facts_checked": ctx.edgar_facts_checked,
            },
            "as_filed": {
                "coverage": ctx.edgar_coverage,
                "period_count": ctx.as_filed_period_count,
                "scores": ctx.as_filed_scores,
                "delta": as_filed_delta,
            },
        }).model_dump()
        await ctx.session.commit()

        # Observability only (Phase 65) -- never allowed to affect an analysis that has
        # already been computed and committed, hence its own try/except.
        try:
            record_analysis_outcome(ctx.scores, confidence)
        except Exception:
            ctx.log.warning("pipeline health record failed", extra={"stage": "score_persist"})
    except Exception as e:
        ctx.log.error(f"Stage score_persist failed: {e}", extra={"stage": "score_persist"})
        await ctx.session.rollback()


async def _stage_report(ctx: StageContext):
    try:
        report_content = await ReportGenerator().generate_report(
            ctx.company, ctx.analysis, ctx.all_flags, ctx.narrative_snapshots
        )
    except Exception as e:
        ctx.log.error(f"Stage report failed: {e}", extra={"stage": "report"})
        report_content = "Report generation failed. Raw scores are available above."

    rep = Report(
        company_id=ctx.company_id,
        analysis_id=ctx.analysis_id,
        content=report_content,
    )
    ctx.session.add(rep)
    await ctx.session.commit()


async def _generate_watchlist_alerts(analysis_id: UUID, company_id: UUID, log: logging.LoggerAdapter):
    """Phase 47 (E-4): every completed analysis that crosses a risk band
    (per FraudScorer.classify_risk) alerts every user watching this company
    -- runs on ANY completion, user- or (the scheduler's) system-triggered.
    Not a STAGES entry: this is a side effect of completion, not a step in
    computing the score, so it must not appear as a pipeline "stage" in
    GET /analysis/{id}/status.

    Phase 48 (A-1): takes plain ids, not a StageContext, and opens its own
    fresh session -- never reuses the stage loop's session, so a prior
    stage's rollback (which expires every object in that session's
    identity map) can never leave the AnalysisResult this reads in a
    stale/expired state. Own try/except -- alerting must never threaten a
    pipeline that just finished successfully.
    """
    try:
        async with AsyncSessionLocal() as session:
            analysis = await session.get(AnalysisResult, analysis_id)
            if analysis is None or analysis.integrity_score is None:
                return

            prev_res = await session.execute(
                select(AnalysisResult)
                .where(
                    AnalysisResult.company_id == company_id,
                    AnalysisResult.status == "complete",
                    AnalysisResult.id != analysis_id,
                )
                .order_by(AnalysisResult.run_at.desc())
                .limit(1)
            )
            previous = prev_res.scalars().first()
            # No prior analysis (first-ever for this company), or either
            # score missing -> nothing real to compare against. Not an error.
            if previous is None or previous.integrity_score is None:
                return

            scorer = FraudScorer()
            previous_risk = scorer.classify_risk(previous.integrity_score)
            new_risk = scorer.classify_risk(analysis.integrity_score)
            if previous_risk == new_risk:
                return  # same band -- not alert-worthy by this step's definition

            watchers_res = await session.execute(
                select(WatchlistItem.user_id).where(WatchlistItem.company_id == company_id)
            )
            user_ids = watchers_res.scalars().all()
            if not user_ids:
                return

            for user_id in user_ids:
                session.add(WatchlistAlert(
                    user_id=user_id,
                    company_id=company_id,
                    analysis_id=analysis_id,
                    previous_score=previous.integrity_score,
                    new_score=analysis.integrity_score,
                    previous_risk=previous_risk,
                    new_risk=new_risk,
                ))
            await session.commit()
    except Exception as e:
        log.error(f"Watchlist alert generation failed: {e}", extra={"stage": "watchlist_alerts"})


STAGES: list[Stage] = [
    Stage("financials", "Fetching financial data...", _stage_financials),
    Stage("forensics", "Running financial forensics...", _stage_forensics),
    Stage("governance", "Evaluating governance indicators...", _stage_governance),
    Stage("narrative", "Processing narrative consistency...", _stage_narrative),
    Stage("news", "Computing Integrity Score...", _stage_news),
    Stage("score_persist", "Computing Integrity Score...", _stage_score_persist),
    Stage("report", "Generating report...", _stage_report),
]


async def run_full_analysis(company_id: UUID, analysis_id: UUID):
    async with AsyncSessionLocal() as session:
        company = await session.get(Company, company_id)
        analysis = await session.get(AnalysisResult, analysis_id)
        if not company or not analysis:
            logger.error(
                f"Analysis {analysis_id}: Company or Analysis missing",
                extra={"correlation_id": str(analysis_id)},
            )
            return

        log = CorrelationLoggerAdapter(logger, {"correlation_id": str(analysis_id), "ticker": company.ticker})

    # ctx accumulates plain-data fields (scores, financial_records, etc.)
    # across the whole run; session/company/analysis are intentionally left
    # unset here and reassigned fresh every stage iteration below.
    ctx = StageContext(analysis_id=analysis_id, company_id=company_id, log=log)

    # Phase 48 (A-1): each stage gets its OWN fresh session and its OWN fresh
    # company/analysis fetch. A stage's rollback expires every object in
    # THAT stage's session only -- it can never leave the NEXT stage reading
    # an expired object, since the next stage never touches this session.
    for stage in STAGES:
        async with AsyncSessionLocal() as stage_session:
            ctx.session = stage_session
            ctx.company = await stage_session.get(Company, company_id)
            ctx.analysis = await stage_session.get(AnalysisResult, analysis_id)
            await update_status(stage_session, analysis_id, stage.status_text)
            log.info("stage started", extra={"stage": stage.name})
            try:
                await stage.fn(ctx)
            except Exception as e:
                log.error(f"Unhandled exception in stage '{stage.name}': {e}", extra={"stage": stage.name})
                # No manual rollback -- exiting this `async with` on exception
                # already closes (and thus rolls back) this stage's session.

    # Phase 48 (A-1): fresh session for the final write -- never reuses the
    # stage loop's session above, so a prior stage's rollback (which expires
    # every object in that session's identity map, including `analysis`/
    # `company`) can never leave this read holding stale state.
    async with AsyncSessionLocal() as session:
        analysis = await session.get(AnalysisResult, analysis_id)
        company = await session.get(Company, company_id)
        if analysis:
            analysis.status = "complete"
        if company:
            company.last_analyzed = datetime.now(timezone.utc).replace(tzinfo=None)
        await session.commit()

    await _generate_watchlist_alerts(analysis_id, company_id, log)
    log.info("analysis complete")
