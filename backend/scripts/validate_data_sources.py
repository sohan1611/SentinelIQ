"""Sweep varied tickers for live financial-data source coverage.

Usage:
    python scripts/validate_data_sources.py [TICKER ...]
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.data_coverage import probe_ticker  # noqa: E402


DEFAULT_TICKERS = (
    "AAPL",  # Mega-cap with uniform statement columns; passed while others broke.
    "KO",  # Phase 67 ragged-columns case: cash-flow sheet is short one period.
    "MSFT",  # Second mega-cap control.
    "JPM",  # Financial sector with different statement line items entirely.
    "CROX",  # Mid-cap coverage check.
    "TM",  # Foreign private issuer (20-F), expected to lack EDGAR XBRL coverage.
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
