import asyncio
import logging
from uuid import UUID
from datetime import datetime

from app.database import AsyncSessionLocal
from app.models.company import Company
from app.models.analysis_result import AnalysisResult
from app.models.financial_data import FinancialData
from app.models.red_flag import RedFlag
from app.models.narrative_snapshot import NarrativeSnapshot
from app.models.report import Report

from app.services.yahoo_finance import fetch_financials
from app.services.news_aggregator import fetch_news_sentiment, fetch_news_text
from app.core.forensics.forensics_runner import ForensicsRunner
from app.core.governance.governance_scorer import GovernanceScorer
from app.core.narrative.consistency_engine import ConsistencyEngine
from app.core.scoring.fraud_scorer import FraudScorer
from app.core.ai.report_generator import ReportGenerator

logger = logging.getLogger(__name__)

async def update_status(session, analysis_id: UUID, stage: str):
    analysis = await session.get(AnalysisResult, analysis_id)
    if analysis:
        analysis.status = f"running:{stage}"
        await session.commit()

async def run_full_analysis(company_id: UUID, analysis_id: UUID):
    async with AsyncSessionLocal() as session:
        try:
            company = await session.get(Company, company_id)
            analysis = await session.get(AnalysisResult, analysis_id)
            if not company or not analysis:
                logger.error(f"Analysis {analysis_id}: Company or Analysis missing")
                return

            all_flags = []
            narrative_snapshots = []
            narrative_snapshot_data = []
            forensics_details = {}
            scores = {}

            # Stage 1
            await update_status(session, analysis_id, "Fetching financial data...")
            financial_records = []
            try:
                raw_financials = await fetch_financials(company.ticker)
                for f in raw_financials:
                    fd = FinancialData(company_id=company_id, **f)
                    session.add(fd)
                    financial_records.append(fd)
                await session.commit()
            except Exception as e:
                logger.error(f"Stage 1 failed for {company.ticker}: {e}")
                await session.rollback()

            # Stage 2 & 3
            await update_status(session, analysis_id, "Running financial forensics...")
            await update_status(session, analysis_id, "Analyzing cash flow patterns...")
            try:
                if financial_records:
                    forensics_res = ForensicsRunner().run_forensics(financial_records)
                    revenue_score = forensics_res["revenue"].score
                    debt_score = forensics_res["debt"].score
                    scores["financial"] = (revenue_score + debt_score) / 2
                    scores["cashflow"] = forensics_res["cashflow"].score
                    scores["earnings"] = forensics_res["earnings"].score
                    scores["debt"] = debt_score

                    forensics_details["revenue"] = forensics_res["revenue"].details
                    forensics_details["cashflow"] = forensics_res["cashflow"].details
                    forensics_details["earnings"] = forensics_res["earnings"].details
                    forensics_details["debt"] = forensics_res["debt"].details

                    for f in forensics_res["all_flags"]:
                        flag_rec = RedFlag(
                            analysis_id=analysis_id,
                            company_id=company_id,
                            flag_type=f.flag_type,
                            severity=f.severity,
                            description=f.description,
                            period=f.period
                        )
                        session.add(flag_rec)
                        all_flags.append(flag_rec)
                    await session.commit()
                else:
                    scores["financial"] = scores["cashflow"] = scores["earnings"] = scores["debt"] = 50.0
            except Exception as e:
                logger.error(f"Stage 2/3 failed for {company.ticker}: {e}")
                await session.rollback()
                scores["financial"] = scores["cashflow"] = scores["earnings"] = scores["debt"] = 50.0

            # Stage 4
            await update_status(session, analysis_id, "Evaluating governance indicators...")
            try:
                news_text = await fetch_news_text(company.name, company.ticker)
                gov_score, gov_flags = await GovernanceScorer().analyze(company.name, news_text)
                scores["governance"] = gov_score
                for gf in gov_flags:
                    flag_rec = RedFlag(
                        analysis_id=analysis_id,
                        company_id=company_id,
                        **gf
                    )
                    session.add(flag_rec)
                    all_flags.append(flag_rec)
                await session.commit()
            except Exception as e:
                logger.error(f"Stage 4 failed for {company.ticker}: {e}")
                await session.rollback()
                scores["governance"] = 50.0

            # Stage 5
            await update_status(session, analysis_id, "Processing narrative consistency...")
            try:
                # We mock management statements from news_text for this prototype
                # In real app, we'd fetch transcripts
                statements = [
                    {"period": "Current", "text": "We see strong growth ahead despite headwinds.", "source": "News"}
                ]
                narrative_score, snaps, cont_flags = await ConsistencyEngine().analyze(company.name, statements)
                scores["narrative"] = narrative_score
                narrative_snapshot_data = snaps

                for s in snaps:
                    sn = NarrativeSnapshot(company_id=company_id, **s)
                    session.add(sn)
                    narrative_snapshots.append(sn)
                    
                for cf in cont_flags:
                    flag_rec = RedFlag(
                        analysis_id=analysis_id,
                        company_id=company_id,
                        **cf
                    )
                    session.add(flag_rec)
                    all_flags.append(flag_rec)
                await session.commit()
            except Exception as e:
                logger.error(f"Stage 5 failed for {company.ticker}: {e}")
                await session.rollback()
                scores["narrative"] = 50.0

            # Stage 6
            await update_status(session, analysis_id, "Computing Integrity Score...")
            try:
                news_sentiment = await fetch_news_sentiment(company.name, company.ticker)
                scores["news"] = news_sentiment
                
                integrity_score = FraudScorer().compute_integrity_score(scores)
                
                analysis.integrity_score = integrity_score
                analysis.financial_score = scores.get("financial")
                analysis.cashflow_score = scores.get("cashflow")
                analysis.governance_score = scores.get("governance")
                analysis.earnings_score = scores.get("earnings")
                analysis.narrative_score = scores.get("narrative")
                analysis.news_score = scores.get("news")
                analysis.module_details = {
                    "scores": scores,
                    "revenue": forensics_details.get("revenue", {}),
                    "cashflow": forensics_details.get("cashflow", {}),
                    "earnings": forensics_details.get("earnings", {}),
                    "debt": forensics_details.get("debt", {}),
                    "narrative": {"snapshots": narrative_snapshot_data},
                }
                await session.commit()
            except Exception as e:
                logger.error(f"Stage 6 failed for {company.ticker}: {e}")
                await session.rollback()
                analysis.status = "failed"
                await session.commit()
                return

            # Stage 7
            await update_status(session, analysis_id, "Generating report...")
            report_content = ""
            try:
                report_content = await ReportGenerator().generate_report(
                    company, analysis, all_flags, narrative_snapshots
                )
            except Exception as e:
                logger.error(f"Stage 7 failed for {company.ticker}: {e}")
                report_content = "Report generation failed. Raw scores are available above."

            rep = Report(
                company_id=company_id,
                analysis_id=analysis_id,
                content=report_content
            )
            session.add(rep)
            
            analysis.status = "complete"
            company.last_analyzed = datetime.utcnow()
            await session.commit()

        except Exception as e:
            logger.error(f"Critical error in analysis pipeline for {analysis_id}: {e}")
            await session.rollback()
            if 'analysis' in locals() and analysis:
                analysis.status = "failed"
                await session.commit()
