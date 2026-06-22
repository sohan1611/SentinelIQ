"""Precision/recall/false-positive-rate validation harness (Phase 43 / H-5).

Runs the real, full 7-stage analysis pipeline directly (bypassing the HTTP
API's free-tier quota gate, the same way backtest_wirecard.py/backtest_enron.py
bypass the route layer -- this is a maintainer-run validation script, not a
user-facing request) against a small, hand-curated, WebSearch-VERIFIED corpus
of real SEC enforcement-action companies (positives) and large, established
companies with no known accounting-fraud history (negatives).

Corpus sourcing (verified 2026-06-22 -- see each entry's `note` for the
specific SEC action/source). This is NOT a systematic pull from SEC's full
AAER archive -- it is a small, honestly-labeled starting corpus, not a
publication-grade academic sample. Sample size is intentionally modest
(13 companies): this is a first version of the harness, meant to be
re-run and grown over time, not a one-shot definitive measurement.

Side effect: this WRITES real Company/AnalysisResult rows to the database
for every ticker below (creating them if they don't already exist) -- these
become normal, searchable, permanent entries in the app, same as any
analysis a real user would trigger. It also makes real yfinance/SEC EDGAR/
Gemini API calls for each of the 13 companies (free tier, no $ cost, but a
real request count and several minutes of wall-clock time).

Run from backend/: .venv\\Scripts\\python.exe scripts\\precision_recall_harness.py
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy.future import select

from app.database import AsyncSessionLocal
from app.models.company import Company
from app.models.analysis_result import AnalysisResult
from app.services.yahoo_finance import fetch_company_info
from app.tasks.analysis_worker import run_full_analysis
from app.core.forensics.eval_metrics import compute_classification_metrics, DEFAULT_THRESHOLD


CORPUS = [
    # --- Positives: real SEC enforcement actions, accounting/disclosure fraud ---
    {"ticker": "LKNCY", "label": "fraud",
     "note": "Luckin Coffee -- $180M SEC penalty Dec 2020; fabricated >$300M in "
             "sales Apr 2019-Jan 2020 (sec.gov/newsroom/press-releases/2020-319)"},
    {"ticker": "KHC", "label": "fraud",
     "note": "Kraft Heinz -- $62M SEC settlement Sept 2021; accounting scheme "
             "2015-2018 understated cost of goods sold "
             "(sec.gov/newsroom/press-releases/2021-174)"},
    {"ticker": "PSIX", "label": "fraud",
     "note": "Power Solutions International -- fraudulently inflated revenue, "
             "misstated financials Q4 2014-Q4 2015"},
    {"ticker": "GE", "label": "fraud",
     "note": "General Electric -- $200M SEC settlement Dec 2020; misled "
             "investors on GE Power profit source and GE Capital/insurance "
             "reserve risk, 2015-2017"},
    {"ticker": "FLR", "label": "fraud",
     "note": "Fluor Corporation -- $14.5M SEC penalty; accounting errors that "
             "materially overstated earnings"},
    {"ticker": "NWL", "label": "fraud",
     "note": "Newell Brands -- $12.5M SEC penalty; misled investors about core "
             "sales growth"},
    {"ticker": "WFC", "label": "fraud",
     "note": "Wells Fargo -- fake-accounts scandal. DIFFERENT FRAUD TYPE "
             "(sales-practices, not financial-statement manipulation) -- "
             "included deliberately to test whether this engine's "
             "accounting-specific forensic signals generalize. Reported "
             "separately from the headline metrics, not folded in silently; "
             "a 'not flagged' result here is an honest scope finding, not a "
             "failure."},
    # --- Negatives: large, established companies with no known accounting-fraud history ---
    {"ticker": "AAPL", "label": "clean", "note": "Large-cap comparable, no known accounting-fraud history"},
    {"ticker": "MSFT", "label": "clean", "note": "Large-cap comparable, no known accounting-fraud history"},
    {"ticker": "KO", "label": "clean", "note": "Large-cap comparable, no known accounting-fraud history"},
    {"ticker": "JNJ", "label": "clean", "note": "Large-cap comparable, no known accounting-fraud history"},
    {"ticker": "PG", "label": "clean", "note": "Large-cap comparable, no known accounting-fraud history"},
    {"ticker": "COST", "label": "clean", "note": "Large-cap comparable, no known accounting-fraud history"},
]


async def get_or_create_company(session, ticker: str) -> Company:
    result = await session.execute(select(Company).where(Company.ticker == ticker))
    company = result.scalars().first()
    if company:
        return company

    # Mirrors routes/company.py's GET /{ticker} "creates if new" behavior.
    info = await fetch_company_info(ticker)
    company = Company(
        name=info.get("longName", ticker),
        ticker=ticker,
        sector=info.get("sector"),
        exchange=info.get("exchange"),
    )
    session.add(company)
    await session.commit()
    await session.refresh(company)
    return company


async def run_one(ticker: str) -> dict:
    async with AsyncSessionLocal() as session:
        company = await get_or_create_company(session, ticker)
        analysis = AnalysisResult(company_id=company.id, status="pending")
        session.add(analysis)
        await session.commit()
        await session.refresh(analysis)
        company_id, analysis_id = company.id, analysis.id

    # run_full_analysis opens its own session internally -- called with bare
    # IDs, exactly how the HTTP route's background_tasks.add_task invokes it.
    await run_full_analysis(company_id, analysis_id)

    async with AsyncSessionLocal() as session:
        refreshed = await session.get(AnalysisResult, analysis_id)
        if not refreshed:
            return {"integrity_score": None, "confidence": None}
        details = refreshed.module_details or {}
        return {
            "integrity_score": refreshed.integrity_score,
            # confidence distinguishes a real signal from an infrastructure-
            # failure fallback that happens to land near 50 -- see Step 3's
            # live run, where rate-limited yfinance/Gemini produced
            # superficially plausible scores with no real data behind them.
            "confidence": details.get("confidence"),
        }


async def main():
    results = []
    for entry in CORPUS:
        print(f"Running {entry['ticker']:8s} ({entry['label']:5s})... ", end="", flush=True)
        try:
            r = await run_one(entry["ticker"])
            print(f"integrity_score={r['integrity_score']} confidence={r['confidence']}")
        except Exception as e:
            print(f"FAILED: {e}")
            r = {"integrity_score": None, "confidence": None}
        results.append({
            "ticker": entry["ticker"], "label": entry["label"],
            "integrity_score": r["integrity_score"], "confidence": r["confidence"],
        })

    print("\n" + "=" * 70)
    print("CORPUS RESULTS")
    print("=" * 70)
    for r in results:
        print(f"  {r['ticker']:8s} {r['label']:6s} integrity_score={r['integrity_score']}  confidence={r['confidence']}")

    # Wells Fargo is a deliberate boundary-case test (a different fraud TYPE)
    # -- reported separately, never folded silently into the headline
    # accounting-fraud-detection metrics.
    main_results = [r for r in results if r["ticker"] != "WFC"]
    wfc_result = next((r for r in results if r["ticker"] == "WFC"), None)

    def print_metrics(label, metrics):
        print(f"\n--- {label} (n={len(main_results)}, threshold={metrics['threshold']}, "
              f"min_confidence={metrics['min_confidence']}) ---")
        print(f"  true_positives:  {metrics['true_positives']}")
        print(f"  false_positives: {metrics['false_positives']}")
        print(f"  true_negatives:  {metrics['true_negatives']}")
        print(f"  false_negatives: {metrics['false_negatives']}")
        print(f"  unscored:               {metrics['unscored']}")
        print(f"  low_confidence_excluded: {metrics['low_confidence_excluded']}")
        print(f"  precision:           {metrics['precision']}")
        print(f"  recall:              {metrics['recall']}")
        print(f"  false_positive_rate: {metrics['false_positive_rate']}")

    print("\n" + "=" * 70)
    print("METRICS (accounting-fraud cases only)")
    print("=" * 70)
    # Reported at two confidence floors: unfiltered (every scored result,
    # including infrastructure-degraded ones) and medium+ (excludes results
    # where the pipeline itself flagged low confidence -- the more honest
    # number when any stage may have been rate-limited).
    print_metrics("ALL SCORED RESULTS (no confidence filter)", compute_classification_metrics(main_results))
    print_metrics("MEDIUM+ CONFIDENCE ONLY", compute_classification_metrics(main_results, min_confidence="medium"))

    if wfc_result:
        score = wfc_result["integrity_score"]
        flagged = score is not None and score <= DEFAULT_THRESHOLD
        print("\n" + "-" * 70)
        print(f"BOUNDARY CASE -- Wells Fargo (WFC): integrity_score={score}, "
              f"confidence={wfc_result['confidence']}, {'FLAGGED' if flagged else 'NOT FLAGGED'}")
        print("Sales-practices fraud, not financial-statement manipulation -- a")
        print("'NOT FLAGGED' result here is an honest scope finding, not a failure.")


if __name__ == "__main__":
    asyncio.run(main())
