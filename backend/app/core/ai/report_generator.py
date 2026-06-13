from pathlib import Path
from typing import List
from app.core.ai.gemini_client import generate_content
from app.models.company import Company
from app.models.analysis_result import AnalysisResult
from app.models.red_flag import RedFlag
from app.models.narrative_snapshot import NarrativeSnapshot
from app.core.scoring.fraud_scorer import FraudScorer

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

        flags_formatted = "\n".join([f"- [{f.severity.upper()}] {f.flag_type.title()}: {f.description} ({f.period or 'N/A'})" for f in flags])
        if not flags_formatted:
            flags_formatted = "None detected."

        # Extract contradictions directly from red flags if narrative type
        contradictions = [f for f in flags if f.flag_type == "narrative"]
        contradictions_formatted = "\n".join([f"- {c.description}" for c in contradictions])
        if not contradictions_formatted:
            contradictions_formatted = "No significant contradictions found."

        risk_level = FraudScorer().classify_risk(analysis.integrity_score or 50.0)

        prompt = prompt_template.format(
            company_name=company.name,
            ticker=company.ticker,
            sector=company.sector or "Unknown",
            score=analysis.integrity_score,
            risk_level=risk_level,
            financial_score=analysis.financial_score,
            cashflow_score=analysis.cashflow_score,
            governance_score=analysis.governance_score,
            earnings_score=analysis.earnings_score,
            narrative_score=analysis.narrative_score,
            flags_formatted=flags_formatted,
            contradictions_formatted=contradictions_formatted
        )

        content = await generate_content(prompt)
        if not content:
            return "Report generation failed. Raw scores are available above."
            
        return content
