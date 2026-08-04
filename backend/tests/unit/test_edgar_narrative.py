"""Phase 58 spike tests: EDGAR-sourced MD&A extraction + the narrative-ready
statement fetcher. Fully mocked -- no network, no Gemini, $0, deterministic.
"""
from unittest.mock import AsyncMock

import httpx
import pytest

import app.services.sec_edgar as sec_edgar_module
from app.services import cache as cache_module
from app.services.sec_edgar import extract_mdna, fetch_management_statements


@pytest.fixture(autouse=True)
def _clear_cache():
    """Every test gets a clean in-memory cache -- fetch_management_statements
    and _fetch_submissions both cache by key, and stale entries from one test
    would otherwise short-circuit the next."""
    cache_module._cache.clear()
    yield
    cache_module._cache.clear()


# ---------------------------------------------------------------------------
# extract_mdna (pure function)
# ---------------------------------------------------------------------------

def test_extract_mdna_returns_none_when_anchor_absent():
    html = "<html><body><p>Just unrelated legal boilerplate text, nothing about results.</p></body></html>"

    assert extract_mdna(html) is None


def test_extract_mdna_skips_the_table_of_contents_occurrence():
    """A 10-K's Table of Contents almost always repeats the MD&A item title.
    The real section content must be extracted, not the empty ToC line."""
    html = """
    <html><body>
    <h2>TABLE OF CONTENTS</h2>
    <p>Item 7. Management's Discussion and Analysis of Financial Condition and Results of Operations</p>
    <p>Item 8. Financial Statements and Supplementary Data</p>
    <h2>PART II</h2>
    <h3>Item 7. Management's Discussion and Analysis of Financial Condition and Results of Operations</h3>
    <p>Revenue grew due to strong demand across all segments this fiscal year.</p>
    <h3>Item 8. Financial Statements and Supplementary Data</h3>
    <p>See accompanying notes to the financial statements.</p>
    </body></html>
    """

    result = extract_mdna(html)

    assert result is not None
    assert "Revenue grew due to strong demand" in result
    assert "See accompanying notes" not in result


def test_extract_mdna_truncates_to_max_chars_when_no_trailing_item_heading():
    long_body = "word " * 5000  # ~25,000 chars, well past MDNA_MAX_CHARS
    html = f"<html><body><h3>Management's Discussion and Analysis</h3><p>{long_body}</p></body></html>"

    result = extract_mdna(html)

    assert result is not None
    assert len(result) <= sec_edgar_module.MDNA_MAX_CHARS


def test_extract_mdna_matches_the_curly_apostrophe_used_by_real_filings():
    """Regression lock for spike bug #1: real (Workiva-generated) EDGAR filings
    render the heading with a curly right-single-quote (U+2019), not an ASCII
    "'". An ASCII-only anchor silently matched ZERO real filings (0 statements
    extracted for every ticker) until this was fixed -- and no straight-quote
    fixture would ever catch a regression back to it."""
    html = (
        "<html><body>"
        "<h3>Item 7. Management’s Discussion and Analysis of Financial "
        "Condition and Results of Operations</h3>"
        "<p>Net sales rose on strong unit demand this period.</p>"
        "<h3>Item 8. Financial Statements</h3><p>See notes.</p>"
        "</body></html>"
    )

    result = extract_mdna(html)

    assert result is not None
    assert "Net sales rose on strong unit demand" in result


def test_extract_mdna_ignores_inline_item_cross_reference_in_opening_paragraph():
    """Regression lock for spike bug #2: a real MD&A section opens with a
    forward-looking-statements paragraph that cross-references OTHER items
    inline (e.g. "...Item 1A of the 2025 Form 10-K..."). The section boundary
    must be the next real "Item N." HEADING (period required), not that inline
    mention -- otherwise the excerpt truncates to the intro paragraph (~100
    chars) and drops the entire real section body. A no-period boundary regex
    passes every other test but fails this one."""
    html = (
        "<html><body>"
        "<h3>Item 7. Management’s Discussion and Analysis</h3>"
        "<p>This section contains forward-looking statements; see the risks "
        "discussed in Part I, Item 1A of the 2025 Form 10-K under Risk Factors. "
        "REAL_MDNA_BODY revenue increased twelve percent driven by services.</p>"
        "<h3>Item 8. Financial Statements</h3><p>See notes.</p>"
        "</body></html>"
    )

    result = extract_mdna(html)

    assert result is not None
    assert "REAL_MDNA_BODY" in result  # inline "Item 1A of" must NOT end the section
    assert "See notes" not in result   # the real "Item 8." heading must


# ---------------------------------------------------------------------------
# fetch_management_statements (mocked HTTP layer)
# ---------------------------------------------------------------------------

class _FakeResponse:
    def __init__(self, *, json_data=None, text="", status_code=200):
        self._json_data = json_data
        self.text = text
        self.status_code = status_code

    def json(self):
        return self._json_data

    def raise_for_status(self):
        if self.status_code >= 400:
            request = httpx.Request("GET", "http://example.test")
            response = httpx.Response(self.status_code, request=request)
            raise httpx.HTTPStatusError("error", request=request, response=response)


class _FakeAsyncClient:
    """Routes GET requests to a canned response keyed by a URL substring."""

    def __init__(self, url_responses: dict[str, _FakeResponse]):
        self._url_responses = url_responses
        self.requested_urls: list[str] = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def get(self, url, headers=None):
        self.requested_urls.append(url)
        for key, resp in self._url_responses.items():
            if key in url:
                return resp
        raise AssertionError(f"Unexpected URL requested in test: {url}")


_MDNA_HTML = (
    "<html><body><h3>Item 7. Management's Discussion and Analysis of Financial "
    "Condition and Results of Operations</h3><p>Revenue increased significantly "
    "this quarter driven by broad-based demand.</p>"
    "<h3>Item 8. Financial Statements</h3><p>See notes.</p></body></html>"
)
_NO_MDNA_HTML = "<html><body><p>Purely procedural filing text, no financial discussion at all.</p></body></html>"

_SUBMISSIONS_JSON = {
    "filings": {
        "recent": {
            # idx0 is an 8-K -- must be filtered out (not in NARRATIVE_FORMS)
            "form": ["8-K", "10-K", "10-Q", "10-Q"],
            "accessionNumber": [
                "0000320193-24-000001",
                "0000320193-24-000002",
                "0000320193-24-000003",
                "0000320193-24-000004",
            ],
            "primaryDocument": ["a.htm", "b.htm", "c.htm", "d.htm"],
            "reportDate": ["2024-01-01", "2024-09-30", "2024-06-30", "2024-03-31"],
            "filingDate": ["2024-01-05", "2024-10-15", "2024-07-15", "2024-04-15"],
        }
    }
}


def _patch_client(monkeypatch, fake_client: _FakeAsyncClient):
    monkeypatch.setattr(sec_edgar_module.httpx, "AsyncClient", lambda timeout: fake_client)


def _patch_cik(monkeypatch, cik: str = "0000320193"):
    monkeypatch.setattr(sec_edgar_module, "get_cik", AsyncMock(return_value=cik))


@pytest.mark.asyncio
async def test_returns_expected_contract_and_filters_to_10k_10q_only(monkeypatch):
    _patch_cik(monkeypatch)
    fake_client = _FakeAsyncClient({
        "data.sec.gov/submissions": _FakeResponse(json_data=_SUBMISSIONS_JSON),
        "000032019324000002": _FakeResponse(text=_MDNA_HTML),  # the 10-K
        "000032019324000003": _FakeResponse(text=_MDNA_HTML),  # the first 10-Q
    })
    _patch_client(monkeypatch, fake_client)

    result = await fetch_management_statements("AAPL", limit=2)

    # 8-K (idx0) must never be requested at all -- filtered before any doc fetch
    assert not any("000032019324000001" in u for u in fake_client.requested_urls)
    assert len(result) == 2
    for s in result:
        assert set(s.keys()) == {"period", "text", "source"}
        assert s["source"].startswith("SEC ")
    periods = {s["period"] for s in result}
    assert periods == {"2024-09-30", "2024-06-30"}


@pytest.mark.asyncio
async def test_respects_the_limit_argument(monkeypatch):
    _patch_cik(monkeypatch)
    fake_client = _FakeAsyncClient({
        "data.sec.gov/submissions": _FakeResponse(json_data=_SUBMISSIONS_JSON),
        "000032019324000002": _FakeResponse(text=_MDNA_HTML),
    })
    _patch_client(monkeypatch, fake_client)

    result = await fetch_management_statements("AAPL", limit=1)

    # Only the single most-recent 10-K/10-Q (the 10-K) should ever be fetched
    assert len(result) == 1
    assert result[0]["period"] == "2024-09-30"
    assert not any("000032019324000003" in u for u in fake_client.requested_urls)


@pytest.mark.asyncio
async def test_skips_a_filing_whose_mdna_extraction_returns_none(monkeypatch):
    _patch_cik(monkeypatch)
    fake_client = _FakeAsyncClient({
        "data.sec.gov/submissions": _FakeResponse(json_data=_SUBMISSIONS_JSON),
        "000032019324000002": _FakeResponse(text=_NO_MDNA_HTML),  # no anchor found
        "000032019324000003": _FakeResponse(text=_MDNA_HTML),
    })
    _patch_client(monkeypatch, fake_client)

    result = await fetch_management_statements("AAPL", limit=2)

    assert len(result) == 1
    assert result[0]["period"] == "2024-06-30"


@pytest.mark.asyncio
async def test_skips_a_filing_whose_doc_fetch_fails(monkeypatch):
    _patch_cik(monkeypatch)
    fake_client = _FakeAsyncClient({
        "data.sec.gov/submissions": _FakeResponse(json_data=_SUBMISSIONS_JSON),
        "000032019324000002": _FakeResponse(status_code=500),
        "000032019324000003": _FakeResponse(text=_MDNA_HTML),
    })
    _patch_client(monkeypatch, fake_client)

    result = await fetch_management_statements("AAPL", limit=2)

    assert len(result) == 1
    assert result[0]["period"] == "2024-06-30"


@pytest.mark.asyncio
async def test_builds_doc_url_with_dashes_stripped_and_cik_unpadded(monkeypatch):
    _patch_cik(monkeypatch, cik="0000320193")
    fake_client = _FakeAsyncClient({
        "data.sec.gov/submissions": _FakeResponse(json_data=_SUBMISSIONS_JSON),
        "000032019324000002": _FakeResponse(text=_MDNA_HTML),
    })
    _patch_client(monkeypatch, fake_client)

    await fetch_management_statements("AAPL", limit=1)

    doc_urls = [u for u in fake_client.requested_urls if "Archives" in u]
    assert len(doc_urls) == 1
    # CIK un-padded (320193, not 0000320193) and accession dashes stripped
    assert "/Archives/edgar/data/320193/000032019324000002/b.htm" in doc_urls[0]


@pytest.mark.asyncio
async def test_returns_empty_list_when_ticker_has_no_cik(monkeypatch):
    monkeypatch.setattr(sec_edgar_module, "get_cik", AsyncMock(return_value=None))

    result = await fetch_management_statements("ZZZNOTREAL")

    assert result == []


@pytest.mark.asyncio
async def test_returns_empty_list_when_submissions_fetch_fails(monkeypatch):
    _patch_cik(monkeypatch)
    fake_client = _FakeAsyncClient({
        "data.sec.gov/submissions": _FakeResponse(status_code=404),
    })
    _patch_client(monkeypatch, fake_client)

    result = await fetch_management_statements("AAPL")

    assert result == []
