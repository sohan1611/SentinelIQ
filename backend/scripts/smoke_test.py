"""Smoke test: run the real analysis core loop against live tickers.

Usage (from backend/):
    python scripts/smoke_test.py AAPL CROX SMAR

Runs run_full_analysis end-to-end against a real DB + Gemini key.
Designed for the founder to:
  - Verify governance flags trace to real headlines (not hallucinated)
  - Sense-check integrity scores against known companies
  - Measure cold-run timing (Render free-tier wall is ~50s per analysis)
  - Surface any yfinance / Gemini stage failures before deploying

Prerequisites:
  - backend/.env has real DATABASE_URL and GEMINI_API_KEY
  - Run `alembic upgrade head` on the target DB before first use
  - Run from the backend/ directory:
      .venv\\Scripts\\python.exe scripts\\smoke_test.py AAPL CROX SMAR  (Windows)
      python scripts/smoke_test.py AAPL CROX SMAR                        (Unix/Mac)

Results are printed to stdout only. No secrets, scores, or company data
are written to any file.
"""

import asyncio
import logging
import sys
import time
from pathlib import Path
from typing import Optional

# Windows consoles default to cp1252, which can't encode the report's box-drawing
# characters and symbols (—, ─, ⚠, ✓). Force UTF-8 so the report doesn't crash
# mid-run on Windows.
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

# Resolve backend/ root so `app.*` imports work regardless of CWD
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Suppress noisy INFO/DEBUG logs from the worker during the smoke run.
# WARNING and ERROR from analysis_worker will still surface (stage failures).
logging.basicConfig(
    level=logging.WARNING,
    format="%(levelname)s %(name)s: %(message)s",
)

from sqlalchemy.future import select  # noqa: E402  (after sys.path insert)

from app.database import AsyncSessionLocal  # noqa: E402
from app.models.analysis_result import AnalysisResult  # noqa: E402
from app.models.company import Company  # noqa: E402
from app.models.red_flag import RedFlag  # noqa: E402
from app.core.scoring.fraud_scorer import FraudScorer  # noqa: E402
from app.services.yahoo_finance import fetch_company_info  # noqa: E402
from app.tasks.analysis_worker import run_full_analysis  # noqa: E402

DIVIDER = "=" * 72
THIN = "-" * 72
RENDER_WARN_SECS = 45  # analyses over this approach the Render ~50s spin-down wall


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _fmt_score(v: Optional[float]) -> str:
    return f"{v:6.1f}" if v is not None else "FAILED"


def _risk(score: Optional[float]) -> str:
    if score is None:
        return "UNKNOWN"
    return FraudScorer().classify_risk(score).upper()


# ---------------------------------------------------------------------------
# per-ticker logic
# ---------------------------------------------------------------------------

async def _ensure_company(session, ticker: str) -> Company:
    """Return existing Company row or create one via yfinance."""
    res = await session.execute(select(Company).where(Company.ticker == ticker))
    company = res.scalars().first()
    if company:
        return company

    print(f"  [{ticker}] Not in DB — fetching company info from yfinance...")
    try:
        info = await fetch_company_info(ticker)
        company = Company(
            name=info.get("longName", ticker),
            ticker=ticker,
            sector=info.get("sector"),
            exchange=info.get("exchange"),
        )
    except Exception as exc:
        print(f"  [{ticker}] WARNING: yfinance company-info fetch failed ({exc}). "
              "Using ticker as company name.")
        company = Company(name=ticker, ticker=ticker)

    session.add(company)
    await session.commit()
    await session.refresh(company)
    return company


async def smoke_ticker(ticker: str) -> dict:
    ticker = ticker.upper()
    print(f"\n{DIVIDER}")
    print(f"  TICKER: {ticker}")
    print(DIVIDER)

    # ── 1. Ensure company + create analysis row ──────────────────────────────
    async with AsyncSessionLocal() as session:
        company = await _ensure_company(session, ticker)
        print(f"  Company : {company.name}")
        print(f"  Sector  : {company.sector or 'N/A'}")

        analysis = AnalysisResult(company_id=company.id, status="pending")
        session.add(analysis)
        await session.commit()
        await session.refresh(analysis)

        company_id = company.id
        analysis_id = analysis.id

    # ── 2. Run full analysis (opens its own session) ─────────────────────────
    short_id = str(analysis_id)[:8]
    print(f"\n  Running analysis (id={short_id}…)")
    t0 = time.monotonic()
    try:
        await run_full_analysis(company_id, analysis_id)
    except Exception as exc:
        print(f"  [ERROR] run_full_analysis raised an unhandled exception: {exc}")
    elapsed = time.monotonic() - t0

    if elapsed > RENDER_WARN_SECS:
        print(f"  ⚠  Elapsed {elapsed:.1f}s — approaches the ~50s Render free-tier "
              "spin-down wall. Consider optimising timeout values or narrative throttle.")
    else:
        print(f"  Elapsed : {elapsed:.1f}s")

    # ── 3. Read back completed results ───────────────────────────────────────
    async with AsyncSessionLocal() as session:
        analysis = await session.get(AnalysisResult, analysis_id)
        if not analysis:
            print("  [ERROR] AnalysisResult row is missing after run — DB issue?")
            return {"ticker": ticker, "status": "missing", "elapsed": elapsed,
                    "integrity_score": None, "confidence": "unknown"}

        flags_res = await session.execute(
            select(RedFlag).where(RedFlag.analysis_id == analysis_id)
        )
        flags = flags_res.scalars().all()

    md = analysis.module_details or {}
    confidence = md.get("confidence", "unknown")

    # ── 4. Print ─────────────────────────────────────────────────────────────
    print(f"\n  STATUS          : {analysis.status}")
    score_str = f"{analysis.integrity_score:.1f}" if analysis.integrity_score is not None else "N/A"
    print(f"  Integrity Score : {score_str}  [{_risk(analysis.integrity_score)}]")
    print(f"  Confidence      : {confidence.upper()}")

    print("\n  MODULE SCORES:")
    print(f"    financial   {_fmt_score(analysis.financial_score)}")
    print(f"    cashflow    {_fmt_score(analysis.cashflow_score)}")
    print(f"    earnings    {_fmt_score(analysis.earnings_score)}")
    print(f"    governance  {_fmt_score(analysis.governance_score)}")
    print(f"    news        {_fmt_score(analysis.news_score)}")
    print(f"    narrative   {_fmt_score(analysis.narrative_score)}"
          "   (zero-weighted — display only)")

    # ── 5. Governance flags (HALLUCINATION REVIEW SECTION) ───────────────────
    gov_flags = [f for f in flags if f.flag_type == "governance"]
    gov_md = md.get("governance", {})
    gov_flag_details = gov_md.get("flags", [])
    detail_by_desc = {d.get("description", ""): d for d in gov_flag_details}
    low_conf = gov_md.get("low_confidence", False)

    print(f"\n  GOVERNANCE FLAGS ({len(gov_flags)})"
          + ("  ⚠ LOW CONFIDENCE (thin news coverage)" if low_conf else "") + ":")

    if not gov_flags:
        print("    (none)")
    else:
        for gf in gov_flags:
            detail = detail_by_desc.get(gf.description, {})
            quote = (detail.get("source_quote") or "").strip()
            print(f"\n    [{gf.severity.upper()}] {gf.description}")
            if quote:
                # Truncate very long quotes for readability
                display = quote if len(quote) <= 220 else quote[:217] + "…"
                print(f"    Source: \"{display}\"")
            else:
                print("    Source: *** MISSING — VERIFY FOR HALLUCINATION ***")

    prov = gov_md.get("provenance", {})
    if isinstance(prov, dict) and prov.get("model_id"):
        print(f"\n  Governance AI : model={prov['model_id']}")

    # ── 6. Financial / forensic red flags ────────────────────────────────────
    fin_flags = [f for f in flags if f.flag_type != "governance"]
    if fin_flags:
        print(f"\n  FINANCIAL / FORENSIC FLAGS ({len(fin_flags)}):")
        for ff in fin_flags:
            print(f"    [{ff.severity.upper()}] [{ff.flag_type}] {ff.description}"
                  + (f"  (period={ff.period})" if ff.period else ""))

    # ── 7. None-score warnings ────────────────────────────────────────────────
    failed_modules = [
        k for k, v in {
            "financial": analysis.financial_score,
            "cashflow": analysis.cashflow_score,
            "earnings": analysis.earnings_score,
            "governance": analysis.governance_score,
            "news": analysis.news_score,
        }.items() if v is None
    ]
    if failed_modules:
        print(f"\n  ⚠  Modules with None score (stage failed): {failed_modules}")
        print("     Check backend logs for the stage error.")

    return {
        "ticker": ticker,
        "status": analysis.status,
        "integrity_score": analysis.integrity_score,
        "confidence": confidence,
        "risk": _risk(analysis.integrity_score),
        "flag_count": len(flags),
        "gov_flags": len(gov_flags),
        "gov_missing_quote": sum(
            1 for gf in gov_flags
            if not detail_by_desc.get(gf.description, {}).get("source_quote", "").strip()
        ),
        "failed_modules": failed_modules,
        "elapsed": elapsed,
    }


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

async def main(tickers: list[str]) -> None:
    if not tickers:
        print(__doc__)
        sys.exit(0)

    print(f"\nSentinelIQ Smoke Test")
    print(f"Tickers : {', '.join(tickers)}")
    print("Reads DATABASE_URL + GEMINI_API_KEY from backend/.env\n")

    results = []
    for ticker in tickers:
        result = await smoke_ticker(ticker)
        results.append(result)

    # ── Summary table ─────────────────────────────────────────────────────────
    print(f"\n\n{DIVIDER}")
    print("  SUMMARY")
    print(DIVIDER)
    print(f"  {'TICKER':<8} {'STATUS':<10} {'SCORE':>6} {'CONF':<8} "
          f"{'RISK':<10} {'FLAGS':>5} {'GOV':>3} {'NO-SRC':>6} {'TIME':>7}")
    print(THIN)
    for r in results:
        score = f"{r['integrity_score']:.1f}" if r["integrity_score"] is not None else "  N/A"
        print(
            f"  {r['ticker']:<8} {r['status']:<10} {score:>6} {r['confidence']:<8} "
            f"{r['risk']:<10} {r['flag_count']:>5} {r['gov_flags']:>3} "
            f"{r['gov_missing_quote']:>6} {r['elapsed']:>6.1f}s"
        )
    print(DIVIDER)
    print("  SCORE = Integrity Score   CONF = confidence tier")
    print("  GOV = governance flag count   NO-SRC = gov flags missing a source quote")

    # ── Actionable issues ─────────────────────────────────────────────────────
    issues = []

    not_complete = [r for r in results if r["status"] != "complete"]
    if not_complete:
        issues.append(f"  ⚠  {len(not_complete)} analysis/analyses did not reach 'complete' status: "
                      f"{[r['ticker'] for r in not_complete]}")

    failed_mod = [r for r in results if r["failed_modules"]]
    if failed_mod:
        for r in failed_mod:
            issues.append(f"  ⚠  {r['ticker']}: modules failed → {r['failed_modules']} "
                          "(check backend logs for stage errors)")

    missing_quotes = [r for r in results if r["gov_missing_quote"] > 0]
    if missing_quotes:
        for r in missing_quotes:
            issues.append(f"  ⚠  {r['ticker']}: {r['gov_missing_quote']} governance flag(s) "
                          "lack a source quote — INVESTIGATE for hallucination")

    slow = [r for r in results if r["elapsed"] > RENDER_WARN_SECS]
    if slow:
        for r in slow:
            issues.append(f"  ⚠  {r['ticker']}: {r['elapsed']:.1f}s — "
                          "may hit Render free-tier spin-down (~50s)")

    if issues:
        print("\n  ISSUES TO INVESTIGATE:")
        for i in issues:
            print(i)
    else:
        print("\n  ✓  All analyses complete — no stage failures, no missing source quotes.")

    print("\n  FOUNDER ACTION: read every governance flag + source quote above.")
    print("  Any flag without a quoted source, or whose quote doesn't match the")
    print("  description, is a potential hallucination. Record the false-positive rate.\n")


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1:]))
