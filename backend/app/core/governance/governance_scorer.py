import re
import logging
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, field_validator

from app.core.ai.gemini_client import generate_json_with_provenance

logger = logging.getLogger(__name__)

# Below this many characters, news_text is shorter than a single typical
# headline — not enough for Gemini to meaningfully evaluate any of the six
# governance event types. Treated as "no signal" (neutral 50, low confidence)
# without spending a Gemini call. See CLAUDE.md Phase 9 amendment.
MIN_NEWS_TEXT_LENGTH = 40

_VALID_SEVERITIES = {"moderate", "high", "severe"}
_SEVERITY_DEDUCTIONS = {"moderate": 15, "high": 25, "severe": 35}


def _normalize(text: str) -> str:
    """Lowercase, collapse whitespace, strip common punctuation for fuzzy grounding match."""
    text = text.lower()
    text = re.sub(r"[''\".,;:!?()\[\]{}\-]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _is_grounded(quote: Optional[str], source_text: str) -> bool:
    """Return True if quote appears verbatim or (normalized) in source_text.

    Verbatim check first; normalized fallback handles minor punctuation/case
    differences without accepting fabricated quotes (Phase 14).
    """
    if not quote or not quote.strip():
        return False
    if quote in source_text:
        return True
    return _normalize(quote) in _normalize(source_text)


class GovernanceEvent(BaseModel):
    """Validated shape for a single governance event returned by Gemini (M-5, Phase 14).

    Unknown severities are normalized to "moderate" with a warning rather than
    silently skipped — a parseable-but-malformed response should still produce
    a deduction rather than a falsely clean score.
    """

    severity: str
    description: str
    source_quote: Optional[str] = None
    event_type: Optional[str] = None
    event_date_approx: Optional[str] = None

    @field_validator("severity", mode="before")
    @classmethod
    def normalize_severity(cls, v) -> str:
        val = str(v).lower().strip()
        if val in _VALID_SEVERITIES:
            return val
        logger.warning(f"GovernanceScorer: unknown severity {v!r}, defaulting to 'moderate'")
        return "moderate"

    @field_validator("description", mode="before")
    @classmethod
    def ensure_description(cls, v) -> str:
        if not v or not str(v).strip():
            return "Governance event detected"
        return str(v)


class GovernanceScorer:
    async def analyze(self, company_name: str, news_text: str) -> tuple[float, list[dict], dict]:
        if len(news_text.strip()) < MIN_NEWS_TEXT_LENGTH:
            return 50.0, [], {
                "model_id": None,
                "prompt": None,
                "raw_response": None,
                "low_confidence": True,
            }

        prompt_path = Path(__file__).parent.parent / "ai" / "prompts" / "governance_prompt.txt"
        with open(prompt_path, "r", encoding="utf-8") as f:
            prompt_template = f.read()

        prompt = prompt_template.format(company_name=company_name, news_text=news_text)

        events, provenance = await generate_json_with_provenance(prompt)
        provenance_record = {
            "model_id": provenance["model_id"],
            "prompt": provenance["prompt"],
            "raw_response": provenance["raw_response"],
            "low_confidence": False,
        }

        if events is None:
            provenance_record["low_confidence"] = True
            return 50.0, [], provenance_record

        if not isinstance(events, list):
            events = []

        score = 100.0
        flags = []

        for raw_event in events:
            if not isinstance(raw_event, dict):
                logger.warning(f"GovernanceScorer: skipping non-dict event: {raw_event!r}")
                continue
            try:
                event = GovernanceEvent.model_validate(raw_event)
            except Exception as e:
                logger.warning(f"GovernanceScorer: invalid event schema, skipping: {e}")
                continue

            if not _is_grounded(event.source_quote, news_text):
                logger.warning(
                    "GovernanceScorer: dropping ungrounded event type=%r "
                    "(source_quote not found in news_text)",
                    event.event_type,
                )
                continue

            score -= _SEVERITY_DEDUCTIONS[event.severity]
            flags.append({
                "flag_type": "governance",
                "severity": event.severity,
                "description": event.description,
                "period": event.event_date_approx[:20] if event.event_date_approx else None,
                "source_quote": event.source_quote,
            })

        score = max(0.0, min(100.0, score))
        return score, flags, provenance_record
