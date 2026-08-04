"""Unit tests for Phase 39 / GOV-2 hardening: Google News queries are
disambiguated by company name + ticker, not the bare ticker alone -- a
governance flag "grounded" in an unrelated headline (e.g. for a short or
word-like ticker) would otherwise get attributed to the wrong company.
"""
import pytest
from unittest.mock import patch, MagicMock
from urllib.parse import quote

from app.services.news_aggregator import _fetch_google_news, _score_headlines


@pytest.mark.asyncio
async def test_query_includes_both_company_name_and_ticker():
    captured_urls = []

    def fake_parse(url):
        captured_urls.append(url)
        feed = MagicMock()
        feed.entries = []
        return feed

    with patch("app.services.news_aggregator.feedparser.parse", side_effect=fake_parse):
        await _fetch_google_news("Apple Inc.", "ZZZTESTTICKER")

    assert len(captured_urls) == 1
    expected_query = quote('"Apple Inc." OR ZZZTESTTICKER')
    assert expected_query in captured_urls[0]


# --- S-1: negation-aware news sentiment (_score_headlines) -------------------
# The previous scorer was a flat +1/-1 keyword bag, blind to word order and
# negation. These tests pin the behaviors that motivated the VADER swap. They
# assert relative ordering and bounds (not exact floats) so they stay robust to
# VADER's precise valences.


def test_score_headlines_empty_is_neutral():
    assert _score_headlines([]) == 50.0
    assert _score_headlines(["", "   "]) == 50.0


def test_score_headlines_positive_above_negative():
    pos = _score_headlines(["company posts record profit and beats estimates"])
    neg = _score_headlines(["company faces fraud investigation, auditor resigned"])
    assert pos > 50.0
    assert neg < 50.0
    assert pos > neg


def test_score_headlines_respects_negation():
    # The core S-1 fix: the old keyword bag scored both of these identically
    # (both contain "fraud"). A negation-aware scorer must rank the negated
    # headline strictly higher than the asserted one.
    negated = _score_headlines(["regulator finds no fraud at the company"])
    asserted = _score_headlines(["regulator alleges fraud at the company"])
    assert negated > asserted


def test_score_headlines_finance_phrases_have_correct_sign():
    # "profit warning" is bad news despite containing "profit"; the old bag
    # netted it to exactly neutral.
    warning = _score_headlines(["airline issues profit warning for the quarter"])
    beat = _score_headlines(["airline reports quarterly profit, beats forecast"])
    assert warning < beat
    # "earnings beat" must read positive even though VADER's base lexicon
    # treats "beat" as violence-negative -- validates the finance overlay.
    assert _score_headlines(["earnings beat expectations"]) > 50.0


def test_score_headlines_is_bounded_and_deterministic():
    headlines = ["record profit", "fraud probe", "shares plunge", "guidance raised"]
    first = _score_headlines(headlines)
    second = _score_headlines(headlines)
    assert first == second
    assert 0.0 <= first <= 100.0
