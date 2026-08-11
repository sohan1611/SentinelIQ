import re
import logging
from pathlib import Path
from typing import List, Dict, Optional

from app.core.ai.gemini_client import generate_json_with_provenance
from app.core.ai.prompt_utils import escape_for_format

logger = logging.getLogger(__name__)


def _normalize(text: str) -> str:
    """Lowercase, collapse whitespace, strip common punctuation for fuzzy grounding match."""
    text = text.lower()
    text = re.sub(r"[''\".,;:!?()\[\]{}\-]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _is_grounded(quote: Optional[str], source_text: str) -> bool:
    """Return True if quote appears verbatim or (normalized) in source_text (Phase 14)."""
    if not quote or not quote.strip():
        return False
    if quote in source_text:
        return True
    return _normalize(quote) in _normalize(source_text)


class ConsistencyEngine:
    async def analyze(self, company_name: str, statements: List[Dict[str, str]]) -> tuple[float, list[dict], list[dict], list[dict]]:
        prompt_path = Path(__file__).parent.parent / "ai" / "prompts" / "narrative_prompt.txt"
        with open(prompt_path, "r", encoding="utf-8") as f:
            prompt_template = f.read()

        snapshots = []
        provenance_records = []
        for stmt in statements:
            period = stmt["period"]
            text = stmt["text"]
            source = stmt["source"]

            prompt = prompt_template.format(
                company_name=escape_for_format(company_name),
                period=escape_for_format(period),
                statement_text=escape_for_format(text),
            )
            result, provenance = await generate_json_with_provenance(prompt)
            provenance_records.append({
                "period": period,
                "model_id": provenance["model_id"],
                "prompt": provenance["prompt"],
                "raw_response": provenance["raw_response"],
            })

            if result is None:
                continue

            source_quote = result.get("source_quote")
            if not _is_grounded(source_quote, text):
                logger.warning(
                    "ConsistencyEngine: dropping ungrounded snapshot period=%r "
                    "(source_quote not found in statement_text)",
                    period,
                )
                continue

            snapshots.append({
                "period": period,
                "statement_text": text,
                "sentiment_label": result.get("sentiment_label", "neutral"),
                "sentiment_score": float(result.get("sentiment_score", 0.0)),
                "source": source,
                "source_quote": source_quote,
            })

        if len(snapshots) < 2:
            return 50.0, snapshots, [], provenance_records

        snapshots = sorted(snapshots, key=lambda x: x["period"])

        contradictions = []
        contradiction_scores = []

        for i in range(1, len(snapshots)):
            prev = snapshots[i - 1]
            curr = snapshots[i]

            # This module measures whether a company's story changes over time, so two
            # statements from the same period cannot contradict each other chronologically.
            # Before this guard, same-day headlines produced the literal
            # "tone shift between 2026-08-10 and 2026-08-10" and a 15/100
            # SEVERE RISK card on the live site.
            if prev["period"] == curr["period"]:
                continue

            diff = abs(curr["sentiment_score"] - prev["sentiment_score"])
            contradiction_scores.append(diff)

            if diff > 0.6:
                contradictions.append({
                    "flag_type": "narrative",
                    "severity": "high" if diff > 0.8 else "moderate",
                    "description": f"Significant tone shift between {prev['period']} and {curr['period']} (Score diff: {diff:.2f})",
                    "period": curr["period"],
                })

        if not contradiction_scores:
            return 50.0, snapshots, contradictions, provenance_records

        avg_contradiction = sum(contradiction_scores) / len(contradiction_scores)
        narrative_score = max(0.0, 100.0 - (avg_contradiction * 100.0))

        return narrative_score, snapshots, contradictions, provenance_records
