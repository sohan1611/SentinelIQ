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
import re
import httpx
from bs4 import BeautifulSoup
from app.config import settings
from app.services import cache

logger = logging.getLogger(__name__)

TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
COMPANYFACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"
REQUEST_TIMEOUT_SECONDS = 20.0

# Phase 58 spike: narrative-quality forms only (10-K/10-Q carry a real MD&A
# section; other filing types on the submissions feed, e.g. 8-K/DEF 14A, do
# not and are skipped).
NARRATIVE_FORMS = {"10-K", "10-Q"}
MDNA_ANCHOR = "management's discussion and analysis"  # display/docstring reference only
# The apostrophe varies by filer/generator: real filings from Workiva-generated
# HTML use a curly right-single-quote (U+2019), not the ASCII "'" -- a literal
# match on MDNA_ANCHOR silently found zero matches on real Apple/Coca-Cola
# filings during this spike (confirmed by direct inspection: "management" was
# present, but the exact ASCII-apostrophe phrase was not). Matching either
# apostrophe variant is required for this to work on real EDGAR HTML at all.
MDNA_ANCHOR_PATTERN = re.compile(r"management[’']s discussion and analysis", re.IGNORECASE)
MDNA_MAX_CHARS = 8000

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


async def _fetch_submissions(cik: str) -> dict | None:
    """Returns the parsed EDGAR filing-history JSON for a CIK (recent filings'
    forms/accession-numbers/primary-documents/dates), or None on a 404 (no
    submissions history) or any other fetch failure. Same shape/caching
    pattern as fetch_company_facts -- filings change far less often than
    market data, so a 7-day cache is safe."""
    cache_key = f"edgar:submissions:{cik}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached if cached != {} else None

    headers = {"User-Agent": settings.SEC_EDGAR_USER_AGENT}
    url = SUBMISSIONS_URL.format(cik=cik)
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
        try:
            resp = await client.get(url, headers=headers)
            if resp.status_code == 404:
                logger.info(f"SEC EDGAR: no submissions history for CIK {cik}")
                cache.set(cache_key, {}, ttl_seconds=604800)
                return None
            resp.raise_for_status()
        except httpx.HTTPError as e:
            logger.warning(f"SEC EDGAR submissions fetch failed for CIK {cik}: {e}")
            return None

    data = resp.json()
    cache.set(cache_key, data, ttl_seconds=604800)  # 7 days
    return data


def extract_mdna(html: str) -> str | None:
    """Best-effort extraction of a 10-K/10-Q's MD&A section from raw filing HTML.

    Phase 58 spike. Filing HTML has no reliable machine-readable section
    markers, and layout varies enormously by filer/era -- a generalized
    parser is out of scope here. Heuristic: locate the LAST case-insensitive
    occurrence of "management's discussion and analysis" in the plain text
    (matching either apostrophe variant -- real Workiva-generated filings use
    a curly "'", not ASCII "'"), on the assumption that earlier occurrences
    are Table-of-Contents/cross-reference mentions and the last one is the
    real heading. From there, take text up to the next top-level "Item N."
    heading (period required -- see the inline comment below) or
    MDNA_MAX_CHARS, whichever comes first.

    KNOWN LIMITATION (found during this spike, confirmed against real live
    AAPL/KO filings, not fixed -- flagged for whoever picks up the H2
    EDGAR-narrative-pipeline work): the "last occurrence = the real heading"
    assumption is not reliable. Some 10-Ks legitimately reference "Management's
    Discussion and Analysis" by name a second time *inside the real section
    itself* (e.g. Apple's 2025 10-K cross-references the *prior* year's 10-K's
    MD&A when explaining an omitted multi-year comparison) -- when that
    self-reference is the last occurrence, extraction starts a paragraph or
    two into the real section rather than at its true heading. Usable in
    practice (the excerpts sampled were still substantive, on-topic MD&A
    prose) but not a formal section boundary. A more robust version would
    need the original DOM structure (heading-tag level, not flattened text)
    to disambiguate a heading from a same-text in-body mention -- that is a
    real implementation cost, not a one-line fix, and is explicitly out of
    scope for this time-boxed spike.

    Returns None if the anchor phrase is not found at all -- callers must
    treat that as "extraction failed for this filing," not an empty section.
    """
    soup = BeautifulSoup(html, "lxml")
    text = soup.get_text(separator=" ")
    text = re.sub(r"\s+", " ", text).strip()

    anchor_matches = list(MDNA_ANCHOR_PATTERN.finditer(text))
    if not anchor_matches:
        return None

    last_match = anchor_matches[-1]
    start = last_match.start()

    # Look for the next top-level "Item N." HEADING strictly after the MD&A
    # heading text itself (offset past it so we don't immediately re-match
    # "Item 7" inside "Item 7. Management's Discussion and Analysis...").
    # The trailing "\." is deliberate and load-bearing: real MD&A sections
    # open with a standard forward-looking-statements paragraph that itself
    # cross-references OTHER item numbers inline (e.g. "...discussed in Part
    # I, Item 1A of the 2025 Form 10-K...") -- without requiring the
    # period, that inline mention is indistinguishable from a real heading
    # and truncates the excerpt to ~100-1200 chars instead of the real,
    # many-page section (confirmed against real AAPL/KO filings during this
    # spike). A real heading is followed by "." (e.g. "Item 8. Financial
    # Statements..."); an inline cross-reference is followed by a word like
    # "of"/"under"/"in", never a period.
    item_heading_pattern = re.compile(r"\bitem\s+\d+[a-z]?\.", re.IGNORECASE)
    next_item_match = item_heading_pattern.search(text, last_match.end() + 20)

    end = min(next_item_match.start(), start + MDNA_MAX_CHARS) if next_item_match else start + MDNA_MAX_CHARS

    excerpt = text[start:end].strip()
    return excerpt if excerpt else None


async def fetch_management_statements(ticker: str, limit: int = 4) -> list[dict]:
    """Phase 58 spike: returns up to `limit` most-recent 10-K/10-Q MD&A
    excerpts as {period, text, source} dicts -- the exact shape
    ConsistencyEngine.analyze() expects (see news_aggregator.py's
    fetch_news_statements for the news-sourced equivalent this is a drop-in,
    richer-text alternative to). Isolated spike function: not called from
    analysis_worker.py or anywhere in the live pipeline. See
    backend/scripts/spike_edgar_narrative.py for a manual demonstration.

    Filings whose HTML doesn't yield an MD&A excerpt (extract_mdna returns
    None) are skipped, not substituted with anything -- an empty return list
    means "no usable narrative found," never a fabricated entry.
    """
    cache_key = f"edgar:mgmt_statements:{ticker}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    cik = await get_cik(ticker)
    if not cik:
        return []

    submissions = await _fetch_submissions(cik)
    if not submissions:
        return []

    recent = submissions.get("filings", {}).get("recent", {})
    forms = recent.get("form", [])
    accession_numbers = recent.get("accessionNumber", [])
    primary_documents = recent.get("primaryDocument", [])
    report_dates = recent.get("reportDate", [])

    candidates = []
    for i, form in enumerate(forms):
        if form in NARRATIVE_FORMS:
            candidates.append({
                "form": form,
                "accession_number": accession_numbers[i],
                "primary_document": primary_documents[i],
                "report_date": report_dates[i],
            })
        if len(candidates) >= limit:
            break

    statements = []
    headers = {"User-Agent": settings.SEC_EDGAR_USER_AGENT}
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
        for c in candidates:
            accession_no_dashes = c["accession_number"].replace("-", "")
            doc_url = (
                f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/"
                f"{accession_no_dashes}/{c['primary_document']}"
            )
            try:
                resp = await client.get(doc_url, headers=headers)
                resp.raise_for_status()
            except httpx.HTTPError as e:
                logger.warning(f"SEC EDGAR filing doc fetch failed for {ticker} {c['form']}: {e}")
                continue

            excerpt = extract_mdna(resp.text)
            if excerpt is None:
                continue

            statements.append({
                "period": c["report_date"],
                "text": excerpt,
                "source": f"SEC {c['form']} MD&A",
            })

    cache.set(cache_key, statements, ttl_seconds=604800)  # 7 days
    return statements


async def fetch_all_concept_histories(ticker: str) -> dict[str, list[dict]] | None:
    """Returns {field_name: [entries]} for every CONCEPT_CANDIDATES field plus
    a best-effort total_debt_approx history, or None if this ticker has no
    CIK at all, or has a CIK but no EDGAR XBRL coverage (e.g. a foreign
    private issuer filing 20-F). The single caller-facing entry point for
    the analysis pipeline (Phase 36) -- callers never need to know about
    get_cik/fetch_company_facts/extract_concept_history individually."""
    cik = await get_cik(ticker)
    if not cik:
        return None
    facts = await fetch_company_facts(cik)
    if not facts:
        return None

    histories = {
        field: extract_concept_history(facts, candidates)
        for field, candidates in CONCEPT_CANDIDATES.items()
    }
    histories["total_debt_approx"] = _total_debt_history(facts)
    return histories


def _total_debt_history(facts: dict) -> list[dict]:
    noncurrent = extract_concept_history(facts, TOTAL_DEBT_COMPONENT_CONCEPTS[:1])
    current = extract_concept_history(facts, TOTAL_DEBT_COMPONENT_CONCEPTS[1:])
    by_key: dict[tuple, dict] = {}
    for e in noncurrent:
        by_key[(e["end"], e["accn"])] = dict(e)
    for e in current:
        key = (e["end"], e["accn"])
        if key in by_key:
            by_key[key]["val"] = by_key[key]["val"] + e["val"]
    return list(by_key.values())


def extract_concept_history(facts: dict, concept_candidates: list[str]) -> list[dict]:
    """Returns EVERY historical entry (every filing, every amendment) across
    EVERY candidate concept tag that has data -- not just the first match.
    A company's tag for the same logical figure can change era (e.g. a
    pre-ASC-606 filer reports "Revenues", then switches to
    "RevenueFromContractWithCustomerExcludingAssessedTax" after adopting
    it) -- "first candidate wins" would silently drop every later era's
    data the moment an earlier candidate has ANY entries (Phase 42 finding:
    surfaced live on real MSFT data, where the old "Revenues" tag matched
    first and silently discarded 131 entries of 2021-2025 revenue under the
    newer tag). This full history, including duplicate periods with
    different filed values, is the raw material Phase 35's restatement
    detector and Phase 42's as-filed adapter both need.

    Each entry: {start, end, val, accn, form, filed} (frame is sometimes
    present too but not required downstream).
    """
    us_gaap = facts.get("facts", {}).get("us-gaap", {})
    merged: list[dict] = []
    for concept in concept_candidates:
        if concept in us_gaap:
            units = us_gaap[concept].get("units", {})
            merged.extend(units.get("USD", []))
    return merged
