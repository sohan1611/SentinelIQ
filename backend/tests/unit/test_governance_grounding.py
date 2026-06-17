"""Unit tests for Phase 14 governance grounding gate.

Verifies that _is_grounded correctly accepts verbatim and normalized quotes,
and that GovernanceScorer.analyze drops ungrounded (hallucinated) events while
keeping grounded ones.
"""
import pytest
from unittest.mock import AsyncMock, patch

from app.core.governance.governance_scorer import (
    GovernanceScorer,
    _is_grounded,
    _normalize,
)


# ---------------------------------------------------------------------------
# _is_grounded unit tests
# ---------------------------------------------------------------------------

def test_verbatim_quote_passes():
    assert _is_grounded("CFO resigned unexpectedly", "Apple CFO resigned unexpectedly amid probe")


def test_empty_quote_fails():
    assert not _is_grounded("", "some news text")


def test_none_quote_fails():
    assert not _is_grounded(None, "some news text")


def test_whitespace_only_quote_fails():
    assert not _is_grounded("   ", "some news text")


def test_fabricated_quote_fails():
    news = "Apple reports record quarterly revenue"
    assert not _is_grounded("CFO resigned amid fraud investigation", news)


def test_normalized_match_passes():
    # Model adds trailing period / different casing — normalized match should pass
    news = "SEC launches inquiry into Apple's accounting practices"
    assert _is_grounded("sec launches inquiry into apple's accounting practices", news)


def test_normalized_punctuation_variant_passes():
    news = "Auditor PwC resigned, citing disagreements with management"
    assert _is_grounded("Auditor PwC resigned citing disagreements with management", news)


def test_quote_not_in_text_fails():
    news = "Apple beats earnings expectations for Q3"
    assert not _is_grounded("independent director resigned over governance concerns", news)


# ---------------------------------------------------------------------------
# GovernanceScorer.analyze grounding integration tests (mocked Gemini)
# ---------------------------------------------------------------------------

NEWS_TEXT = (
    "Apple CFO Luca Maestri unexpectedly resigned on Monday. "
    "SEC launches inquiry into Apple's accounting practices. "
    "Apple reports record quarterly revenue."
)

GROUNDED_EVENT = {
    "event_type": "executive_departure",
    "event_date_approx": "2024-01-15",
    "severity": "high",
    "description": "CFO resigned",
    "source_quote": "Apple CFO Luca Maestri unexpectedly resigned on Monday",
}

UNGROUNDED_EVENT = {
    "event_type": "restatement",
    "event_date_approx": "2024-01-10",
    "severity": "severe",
    "description": "Financial restatement announced",
    "source_quote": "Apple admitted to fabricating revenue figures for three years",
}


@pytest.mark.asyncio
async def test_grounded_event_is_kept():
    provenance_stub = {
        "text": "[]",
        "prompt": "...",
        "model_id": "gemini-2.5-flash",
        "raw_response": None,
    }
    with patch(
        "app.core.governance.governance_scorer.generate_json_with_provenance",
        new=AsyncMock(return_value=([GROUNDED_EVENT], provenance_stub)),
    ):
        scorer = GovernanceScorer()
        score, flags, provenance = await scorer.analyze("Apple Inc.", NEWS_TEXT)

    assert len(flags) == 1
    assert flags[0]["description"] == "CFO resigned"
    assert flags[0]["source_quote"] == GROUNDED_EVENT["source_quote"]
    assert score == 75.0  # 100 - 25 (high severity)


@pytest.mark.asyncio
async def test_hallucinated_event_is_dropped():
    provenance_stub = {
        "text": "[]",
        "prompt": "...",
        "model_id": "gemini-2.5-flash",
        "raw_response": None,
    }
    with patch(
        "app.core.governance.governance_scorer.generate_json_with_provenance",
        new=AsyncMock(return_value=([UNGROUNDED_EVENT], provenance_stub)),
    ):
        scorer = GovernanceScorer()
        score, flags, provenance = await scorer.analyze("Apple Inc.", NEWS_TEXT)

    assert len(flags) == 0
    assert score == 100.0  # no grounded events → no deductions


@pytest.mark.asyncio
async def test_mixed_events_only_grounded_kept():
    provenance_stub = {
        "text": "[]",
        "prompt": "...",
        "model_id": "gemini-2.5-flash",
        "raw_response": None,
    }
    events = [GROUNDED_EVENT, UNGROUNDED_EVENT]
    with patch(
        "app.core.governance.governance_scorer.generate_json_with_provenance",
        new=AsyncMock(return_value=(events, provenance_stub)),
    ):
        scorer = GovernanceScorer()
        score, flags, provenance = await scorer.analyze("Apple Inc.", NEWS_TEXT)

    assert len(flags) == 1
    assert flags[0]["source_quote"] == GROUNDED_EVENT["source_quote"]
    assert score == 75.0


@pytest.mark.asyncio
async def test_event_missing_source_quote_is_dropped():
    event_no_quote = {
        "event_type": "sec_inquiry",
        "event_date_approx": "2024-02-01",
        "severity": "moderate",
        "description": "SEC inquiry",
        # source_quote intentionally absent
    }
    provenance_stub = {
        "text": "[]",
        "prompt": "...",
        "model_id": "gemini-2.5-flash",
        "raw_response": None,
    }
    with patch(
        "app.core.governance.governance_scorer.generate_json_with_provenance",
        new=AsyncMock(return_value=([event_no_quote], provenance_stub)),
    ):
        scorer = GovernanceScorer()
        score, flags, provenance = await scorer.analyze("Apple Inc.", NEWS_TEXT)

    assert len(flags) == 0
    assert score == 100.0
