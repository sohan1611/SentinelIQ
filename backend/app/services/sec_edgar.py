"""SEC EDGAR XBRL company-facts client.

Free, keyless data.sec.gov endpoints -- the only requirement is a descriptive
User-Agent per SEC's fair-access policy (~10 req/sec guidance). One
fetch_company_facts() call returns a company's ENTIRE XBRL history in a
single JSON blob (every concept, every filing, every amendment) -- there is
no per-concept network call, so normal per-analysis usage (one company at a
time) never approaches the rate limit on its own.

Phase 34 scope: data fetch + extraction only. No scoring, no RedFlags, no
pipeline wiring -- see MASTER_IMPLEMENTATION_PLAN.md Phase 34/35.
"""
import logging
import httpx
from app.config import settings
from app.services import cache

logger = logging.getLogger(__name__)

TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
COMPANYFACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
REQUEST_TIMEOUT_SECONDS = 20.0

# XBRL us-gaap concept tags vary by company and era for the same logical
# figure (e.g. a pre-2018 filer vs. one that adopted ASC 606 revenue
# recognition). Tried in order; first match wins -- same pattern as
# yahoo_finance.py's get_val(df, row_names).
CONCEPT_CANDIDATES: dict[str, list[str]] = {
    "revenue": ["Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax", "SalesRevenueNet"],
    "net_income": ["NetIncomeLoss"],
    "operating_cf": ["NetCashProvidedByUsedInOperatingActivities"],
    "total_assets": ["Assets"],
    "accounts_recv": ["AccountsReceivableNetCurrent"],
}

# total_debt has no single universal XBRL tag the way Assets does -- yfinance
# computes it internally from underlying line items. Best-effort approximation:
# sum whichever of these are present for a period. None if neither is present
# (never silently treated as zero -- matches this codebase's "absence is not
# neutral" rule).
TOTAL_DEBT_COMPONENT_CONCEPTS = ["LongTermDebtNoncurrent", "LongTermDebtCurrent"]


def _normalize_cik(cik: str | int) -> str:
    """CIK as used in companyfacts URLs: zero-padded to 10 digits, no leading zeros stripped."""
    return str(cik).zfill(10)


async def _fetch_ticker_cik_map() -> dict[str, str]:
    cache_key = "edgar:ticker_cik_map"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    headers = {"User-Agent": settings.SEC_EDGAR_USER_AGENT}
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
        try:
            resp = await client.get(TICKERS_URL, headers=headers)
            resp.raise_for_status()
        except httpx.HTTPError as e:
            logger.warning(f"SEC EDGAR ticker map fetch failed: {e}")
            return {}

    data = resp.json()
    # data.sec.gov's company_tickers.json is {"0": {"cik_str": 320193, "ticker": "AAPL", ...}, "1": {...}, ...}
    mapping = {
        entry["ticker"].upper(): _normalize_cik(entry["cik_str"])
        for entry in data.values()
        if entry.get("ticker") and entry.get("cik_str") is not None
    }
    cache.set(cache_key, mapping, ttl_seconds=86400)  # 24h -- this list changes rarely
    return mapping


async def get_cik(ticker: str) -> str | None:
    mapping = await _fetch_ticker_cik_map()
    return mapping.get(ticker.upper())


async def fetch_company_facts(cik: str) -> dict | None:
    """Returns the full parsed companyfacts JSON, or None if this CIK has no
    EDGAR XBRL coverage (404 -- common for foreign private issuers who file
    20-F, or any non-XBRL filer) or the request otherwise fails."""
    cache_key = f"edgar:companyfacts:{cik}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached if cached != {} else None  # cache.get can't distinguish None from "not cached"

    headers = {"User-Agent": settings.SEC_EDGAR_USER_AGENT}
    url = COMPANYFACTS_URL.format(cik=cik)
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
        try:
            resp = await client.get(url, headers=headers)
            if resp.status_code == 404:
                logger.info(f"SEC EDGAR: no XBRL coverage for CIK {cik}")
                cache.set(cache_key, {}, ttl_seconds=604800)  # cache the negative result too -- 7 days
                return None
            resp.raise_for_status()
        except httpx.HTTPError as e:
            logger.warning(f"SEC EDGAR companyfacts fetch failed for CIK {cik}: {e}")
            return None

    data = resp.json()
    cache.set(cache_key, data, ttl_seconds=604800)  # 7 days -- filings change far less often than market data
    return data


def extract_concept_history(facts: dict, concept_candidates: list[str]) -> list[dict]:
    """Returns EVERY historical entry (every filing, every amendment) for the
    first candidate concept found, not just the latest value -- this full
    history, including duplicate periods with different filed values, is the
    raw material Phase 35's restatement detector needs.

    Each entry: {start, end, val, accn, form, filed} (frame is sometimes
    present too but not required downstream).
    """
    us_gaap = facts.get("facts", {}).get("us-gaap", {})
    for concept in concept_candidates:
        if concept in us_gaap:
            units = us_gaap[concept].get("units", {})
            usd_entries = units.get("USD", [])
            if usd_entries:
                return usd_entries
    return []
