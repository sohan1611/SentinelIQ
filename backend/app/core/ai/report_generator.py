import asyncio
from pathlib import Path
from typing import List
from app.core.ai.gemini_client import generate_content
from app.core.ai.prompt_utils import escape_for_format
from app.models.company import Company
from app.models.analysis_result import AnalysisResult
from app.models.red_flag import RedFlag
from app.models.narrative_snapshot import NarrativeSnapshot
from app.core.scoring.fraud_scorer import FraudScorer

# Outer hard deadline for the entire report stage (single call + any retries).
# gemini_client._call_with_backoff already enforces 30s per attempt; this cap
# ensures the stage never holds the pipeline longer than 45s regardless of
# backoff sleep accumulation or network-level hang.
REPORT_STAGE_TIMEOUT_SECONDS = 45.0


def _fmt_score(score) -> str:
    """Return a human-readable score string for the LLM prompt. None → 'Unavailable'."""
    if score is None:
        return "Unavailable"
    return str(round(score, 1))


class ReportGenerator:
    async def generate_report(
        self,
        company: Company,
        analysis: AnalysisResult,
        flags: List[RedFlag],
        narrative_snapshots: List[NarrativeSnapshot]
    ) -> str:
        prompt_path = Path(__file__).parent / "prompts" / "report_prompt.txt"
        with open(prompt_path, "r", encoding="utf-8") as f:
            prompt_template = f.read()

        flags_formatted = "\n".join([
            f"- [{f.severity.upper()}] {f.flag_type.title()}: {f.description} ({f.period or 'N/A'})"
            for f in flags
        ])
        if not flags_formatted:
            flags_formatted = "None detected."

        tone_shifts = (analysis.module_details or {}).get("narrative", {}).get("tone_shifts", [])
        contradictions_formatted = "\n".join([f"- {c['description']}" for c in tone_shifts])
        if not contradictions_formatted:
            contradictions_formatted = "No significant news tone shifts detected."

        risk_level = FraudScorer().classify_risk(analysis.integrity_score or 50.0)

        # Guard against fabricated financial commentary when the data source
        # returned nothing (yahoo_finance 429 / rate-limit).
        no_financial_data = (
            analysis.financial_score is None
            and analysis.cashflow_score is None
            and analysis.earnings_score is None
        )
        if no_financial_data:
            financial_data_note = (
                "IMPORTANT DATA LIMITATION: Financial statement data was unavailable for this "
                "company (the data provider returned no financial records). The "
                "## Financial Analysis section must clearly acknowledge this gap and must not "
                "fabricate, infer, or estimate any financial metrics. State that the Integrity "
                "Score was computed from governance and news signals only. Do not invent revenue "
                "figures, margin trends, cash flow commentary, or any other financial metric."
            )
        else:
            financial_data_note = ""

        prompt = prompt_template.format(
            company_name=escape_for_format(company.name),
            ticker=escape_for_format(company.ticker),
            sector=escape_for_format(company.sector or "Unknown"),
            score=analysis.integrity_score,
            risk_level=risk_level,
            financial_score=_fmt_score(analysis.financial_score),
            cashflow_score=_fmt_score(analysis.cashflow_score),
            governance_score=_fmt_score(analysis.governance_score),
            earnings_score=_fmt_score(analysis.earnings_score),
            narrative_score=_fmt_score(analysis.narrative_score),
            flags_formatted=escape_for_format(flags_formatted),
            contradictions_formatted=escape_for_format(contradictions_formatted),
            financial_data_note=financial_data_note,
        )

        try:
            content = await asyncio.wait_for(
                generate_content(prompt),
                timeout=REPORT_STAGE_TIMEOUT_SECONDS,
            )
        except asyncio.TimeoutError:
            content = None

        if not content:
            return "Report generation failed. Raw scores are available above."

        return content
