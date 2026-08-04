"""Phase 58 SPIKE: can SEC EDGAR MD&A text replace Google-News headlines as
the source for the narrative module's ConsistencyEngine?

This is a time-boxed proof-of-concept, NOT a production feature. It is fully
isolated from the live pipeline:
  - analysis_worker.py's _stage_narrative is untouched (still calls
    news_aggregator.fetch_news_statements).
  - fraud_scorer.py's BASE_WEIGHTS is untouched (narrative stays zero-weight).
Nothing here is wired into any route, background task, or the scoring model.

Usage (from backend/):
    .venv\\Scripts\\python.exe scripts\\spike_edgar_narrative.py                (Windows, dry-run)
    python scripts/spike_edgar_narrative.py                                     (Unix/Mac, dry-run)
    .venv\\Scripts\\python.exe scripts\\spike_edgar_narrative.py AAPL KO MSFT   (custom tickers)
    .venv\\Scripts\\python.exe scripts\\spike_edgar_narrative.py --analyze       (also calls Gemini)

Modes:
  DEFAULT (no flags): fetches + extracts EDGAR MD&A text and prints it. $0,
    no network calls beyond free/keyless SEC EDGAR endpoints, no Gemini call.
  --analyze: additionally runs ConsistencyEngine().analyze() on the EDGAR
    statements -- this calls Gemini and costs against the daily budget.
    Requires GEMINI_API_KEY in backend/.env. Opt-in only; run deliberately,
    not as part of routine verification.
"""
import asyncio
import sys
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.sec_edgar import fetch_management_statements  # noqa: E402
from app.core.narrative.consistency_engine import ConsistencyEngine  # noqa: E402

DIVIDER = "=" * 72
THIN = "-" * 72
DEFAULT_TICKERS = ["AAPL", "KO"]
PREVIEW_CHARS = 300


async def _dry_run(ticker: str) -> list[dict]:
    print(f"\n[{ticker}] fetching EDGAR MD&A statements (free, no Gemini call)...")
    statements = await fetch_management_statements(ticker)
    print(f"[{ticker}] {len(statements)} statement(s) extracted")
    for s in statements:
        preview = s["text"][:PREVIEW_CHARS].replace("\n", " ")
        print(THIN)
        print(f"  period: {s['period']}")
        print(f"  source: {s['source']}")
        print(f"  text length: {len(s['text'])} chars")
        print(f"  preview: {preview}...")
    return statements


async def _analyze(ticker: str, statements: list[dict]) -> None:
    if len(statements) < 2:
        print(f"[{ticker}] fewer than 2 statements -- ConsistencyEngine needs >=2, skipping --analyze")
        return

    print(f"[{ticker}] running ConsistencyEngine.analyze() -- THIS CALLS GEMINI (costs budget)...")
    narrative_score, snapshots, contradictions, _provenance = await ConsistencyEngine().analyze(
        ticker, statements
    )
    print(f"[{ticker}] narrative_score: {narrative_score}")
    print(f"[{ticker}] grounded snapshots: {len(snapshots)} (of {len(statements)} statements submitted)")
    for snap in snapshots:
        print(f"    {snap['period']}: {snap['sentiment_label']} ({snap['sentiment_score']:.2f})")
    if contradictions:
        print(f"[{ticker}] tone-shift contradictions:")
        for c in contradictions:
            print(f"    {c['period']}: {c['severity']} -- {c['description']}")
    else:
        print(f"[{ticker}] no tone-shift contradictions detected")


async def main():
    args = sys.argv[1:]
    do_analyze = "--analyze" in args
    tickers = [a for a in args if not a.startswith("--")] or DEFAULT_TICKERS

    print(DIVIDER)
    print("PHASE 58 SPIKE: EDGAR-sourced narrative (isolated, NOT wired into production)")
    print(f"Mode: {'DRY-RUN + --analyze (calls Gemini, costs budget)' if do_analyze else 'DRY-RUN only (free, no Gemini call)'}")
    print(f"Tickers: {tickers}")
    print(DIVIDER)

    for ticker in tickers:
        statements = await _dry_run(ticker)
        if do_analyze:
            await _analyze(ticker, statements)

    print(f"\n{DIVIDER}\nDone. This spike is isolated -- no production code path was touched.\n{DIVIDER}")


if __name__ == "__main__":
    asyncio.run(main())
