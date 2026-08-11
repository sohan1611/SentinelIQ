"""Sweep varied tickers for live financial-data source coverage.

Makes NO Gemini calls and writes NOTHING to the database, so it costs nothing to
run and never touches the free-tier analysis quota.

Usage:
    python scripts/validate_data_sources.py [TICKER ...]

Reading the results -- not every non-"ok" verdict is a bug:

  * "degraded" with 0 MD&A statements is EXPECTED for a foreign private issuer.
    TM and BABA file 20-F, not 10-K/10-Q, so there is no MD&A to extract and the
    narrative module correctly falls back to news headlines. Treat this as a
    coverage limit of the source, not a defect.

  * "failed" with `503: FINANCIAL_DATA_UNAVAILABLE` AND no EDGAR CIK almost
    certainly means the ticker no longer trades, not that anything is broken.
    Verified example: SMAR (Smartsheet, taken private in early 2025) returns
    empty income/balance/cash-flow frames, `quoteType='NONE'`, no name, no
    exchange, and no CIK. Note the 503 is nominally "retriable" -- yahoo_finance
    raises it whenever all three statements come back empty, on the assumption
    that a real ticker with empty sheets is being rate-limited. For a delisted
    ticker that condition is permanent, so a watchlist entry for such a company
    would be re-attempted indefinitely. Low impact today (it degrades exactly
    like any other missing feed) but worth knowing before chasing it as a bug.

  * "failed" on a ticker that IS live, or a sudden change in verdict for one of
    the defaults below, is the signal this script exists to catch.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.data_coverage import probe_ticker  # noqa: E402


# Every entry earns its place by covering a DIFFERENT shape of filer. The point is
# breadth, not count: Phase 67 was invisible for as long as it was because AAPL --
# whose three statements happen to share identical period columns -- passed every
# check while KO was completely broken. All of these were verified live on
# 2026-08-11; the expected results are recorded so a future change in verdict is
# obviously a regression rather than a mystery.
DEFAULT_TICKERS = (
    "AAPL",  # Mega-cap, uniform statement columns; passed while others broke. -> ok
    "KO",  # Phase 67 ragged-columns case: cash-flow sheet short one period.  -> ok
    "MSFT",  # Second mega-cap control.                                        -> ok
    "JPM",  # Bank: different statement line items entirely.                   -> ok
    "CROX",  # Mid-cap.                                                        -> ok
    "O",  # REIT: FFO-oriented statements, unlike an operating company.         -> ok
    "MRNA",  # Biotech that can post no revenue at all in a period.            -> ok
    "UPST",  # Small-cap fintech; carries 5 usable periods, not 4.             -> ok
    "NEE",  # Utility: heavy capex/regulated-asset balance sheet.              -> ok
    "TM",  # Foreign private issuer (20-F): no 10-K/10-Q, so no MD&A.    -> degraded
    "BABA",  # Second 20-F filer, confirming the fallback is not TM-specific.
    #        -> degraded (both are CORRECT: narrative falls back to news headlines)
)


async def main() -> int:
    """Run the probes sequentially to keep Yahoo and SEC request rates polite."""
    tickers = sys.argv[1:] or DEFAULT_TICKERS

    print("SentinelIQ data-source coverage sweep")
    print("This makes NO Gemini calls and writes NOTHING to the database.")
    print()
    print(
        f"{'TICKER':<8} {'STATUS':<10} {'USABLE':>6} {'EDGAR':<5} "
        f"{'MD&A':>4} {'MD&A PERIODS':>12} {'NARRATIVE SOURCE':<18}"
    )
    print("-" * 80)

    results: list[dict] = []
    for ticker in tickers:
        result = await probe_ticker(ticker)
        results.append(result)
        edgar = "yes" if result["edgar_covered"] else "no"
        print(
            f"{result['ticker']:<8} {result['status']:<10} "
            f"{result['usable_periods']:>6} {edgar:<5} "
            f"{result['mdna_statements']:>4} {result['mdna_distinct_periods']:>12} "
            f"{result['narrative_source_would_be']:<18}"
        )

    print("\nISSUES")
    non_ok_results = [result for result in results if result["status"] != "ok"]
    if not non_ok_results:
        print("None.")
    else:
        for result in non_ok_results:
            print(f"{result['ticker']} ({result['status']}):")
            for issue in result["issues"]:
                print(f"  - {issue}")

    # This supports a future scheduled check; do not wire this online sweep into CI.
    return 1 if any(result["status"] == "failed" for result in results) else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
