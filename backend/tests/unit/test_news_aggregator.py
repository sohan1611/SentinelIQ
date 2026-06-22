"""Unit tests for Phase 39 / GOV-2 hardening: Google News queries are
disambiguated by company name + ticker, not the bare ticker alone -- a
governance flag "grounded" in an unrelated headline (e.g. for a short or
word-like ticker) would otherwise get attributed to the wrong company.
"""
import pytest
from unittest.mock import patch, MagicMock
from urllib.parse import quote

from app.services.news_aggregator import _fetch_google_news


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
