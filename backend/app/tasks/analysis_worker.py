import logging
from dataclasses import dataclass, field
from typing import Awaitable, Callable
from uuid import UUID
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models.company import Company
from app.models.analysis_result import AnalysisResult
from app.models.financial_data import FinancialData
from app.models.red_flag import RedFlag
from app.models.narrative_snapshot import NarrativeSnapshot
from app.models.report import Report

from app.services.yahoo_finance import fetch_financials
from app.services.news_aggregator import fetch_news_sentiment, fetch_news_text, fetch_news_statements
from app.core.forensics.forensics_runner import ForensicsRunner
from app.core.governance.governance_scorer import GovernanceScorer
from app.core.narrative.consistency_engine import ConsistencyEngine
from app.core.scoring.fraud_scorer import FraudScorer
from app.core.ai.report_generator import ReportGenerator
from app.logging_config import CorrelationLoggerAdapter
from app.schemas.analysis import ModuleDetails, CURRENT_SCHEMA_VERSION

logger = logging.getLogger(__name__)


async def update_status(session: AsyncSession, analysis_id: UUID, stage: str):
    analysis = await session.get(AnalysisResult, analysis_id)
    if analysis:
        analysis.status = f"running:{stage}"
        await session.commit()


@dataclass
class StageContext:
    session: AsyncSession
    company: Company
    analysis: AnalysisResult
    analysis_id: UUID
    company_id: UUID
    log: logging.LoggerAdapter
    scores: dict = field(default_factory=dict)
    forensics_details: dict = field(default_factory=dict)
    financial_records: list = field(default_factory=list)
    all_flags: list = field(default_factory=list)
    narrative_snapshots: list = field(default_factory=list)
    narrative_snapshot_data: list = field(default_factory=list)
    narrative_provenance: list = field(default_factory=list)
    narrative_tone_shifts: list = field(default_factory=list)
    governance_provenance: dict = field(default_factory=dict)
    governance_flags: list = field(default_factory=list)
    financial_data_status: str = "ok"


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
            return

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
        statements = await fetch_news_statements(ctx.company.name, ctx.company.ticker, limit=2)
        if len(statements) < 2:
            ctx.scores["narrative"] = 50.0
            return

        narrative_score, snaps, cont_flags, provenance = await ConsistencyEngine().analyze(
            ctx.company.name, statements
        )
        ctx.scores["narrative"] = narrative_score
        ctx.narrative_snapshot_data = snaps
        ctx.narrative_provenance = provenance

        for s in snaps:
            sn = NarrativeSnapshot(company_id=ctx.company_id, fetched_at=datetime.now(timezone.utc), **s)
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
            },
            "governance": {
                "provenance": ctx.governance_provenance,
                "low_confidence": ctx.governance_provenance.get("low_confidence", False),
                "flags": ctx.governance_flags,
            },
            "financial_data_status": ctx.financial_data_status if ctx.financial_data_status != "ok" else None,
        }).model_dump()
        await ctx.session.commit()
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

        ctx = StageContext(
            session=session,
            company=company,
            analysis=analysis,
            analysis_id=analysis_id,
            company_id=company_id,
            log=log,
        )

        for stage in STAGES:
            await update_status(session, analysis_id, stage.status_text)
            log.info("stage started", extra={"stage": stage.name})
            try:
                await stage.fn(ctx)
            except Exception as e:
                log.error(f"Unhandled exception in stage '{stage.name}': {e}", extra={"stage": stage.name})
                try:
                    await session.rollback()
                except Exception:
                    pass

        analysis.status = "complete"
        company.last_analyzed = datetime.now(timezone.utc)
        await session.commit()
        log.info("analysis complete")
