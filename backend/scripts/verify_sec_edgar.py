"""Phase 34 verification: SEC EDGAR data fetch + storage, against the real API and real DB.

Usage (from backend/):
    .venv\\Scripts\\python.exe scripts\\verify_sec_edgar.py   (Windows)
    python scripts/verify_sec_edgar.py                         (Unix/Mac)

Checks, per Phase 34's success criteria (MASTER_IMPLEMENTATION_PLAN.md):
  - Ticker->CIK lookup for 5 real companies
  - Full concept history (not just latest) for revenue, net_income,
    operating_cf, total_assets, accounts_recv -- plus a best-effort
    total_debt approximation
  - Apple's known FY2007 NetIncomeLoss restatement (10-K vs 10-K/A) is
    independently reproduced by extract_concept_history(), not asserted
  - A nonexistent ticker (no CIK at all) and a real foreign filer (CIK
    exists, no XBRL companyfacts) both degrade to None/empty, never raise
  - Persists EdgarFinancialFact rows for the real companies tested

No scoring, no RedFlags, no pipeline wiring -- foundation only.
"""
import asyncio
import sys
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy.future import select  # noqa: E402

from app.database import AsyncSessionLocal  # noqa: E402
from app.models.company import Company  # noqa: E402
from app.models.edgar_fact import EdgarFinancialFact  # noqa: E402
from app.services import sec_edgar  # noqa: E402

DIVIDER = "=" * 72
TEST_TICKERS = ["AAPL", "MSFT", "TSLA", "JPM", "KO"]
NONEXISTENT_TICKER = "ZZZZNOTREAL"
FOREIGN_FILER_TICKER = "TM"  # Toyota -- files 20-F, expected (not asserted) to lack XBRL companyfacts


async def get_or_create_company(session, ticker: str) -> Company:
    result = await session.execute(select(Company).where(Company.ticker == ticker))
    company = result.scalars().first()
    if company:
        return company
    company = Company(name=ticker, ticker=ticker)
    session.add(company)
    await session.commit()
    await session.refresh(company)
    return company


async def persist_facts(session, company: Company, concept: str, entries: list[dict]) -> int:
    count = 0
    for e in entries:
        session.add(EdgarFinancialFact(
            company_id=company.id,
            concept=concept,
            period_start=e.get("start"),
            period_end=e["end"],
            value=e["val"],
            accession_number=e["accn"],
            form_type=e["form"],
            filed_date=e["filed"],
        ))
        count += 1
    await session.commit()
    return count


async def fetch_total_debt_history(facts: dict) -> list[dict]:
    """Best-effort approximation: sum LongTermDebtNoncurrent + LongTermDebtCurrent
    per (end, accn) pair where both are present. No single XBRL tag covers this
    the way Assets does -- see sec_edgar.py's TOTAL_DEBT_COMPONENT_CONCEPTS."""
    noncurrent = sec_edgar.extract_concept_history(facts, ["LongTermDebtNoncurrent"])
    current = sec_edgar.extract_concept_history(facts, ["LongTermDebtCurrent"])
    by_key = {}
    for e in noncurrent:
        by_key[(e["end"], e["accn"])] = {"end": e["end"], "accn": e["accn"], "form": e["form"], "filed": e["filed"], "val": e["val"]}
    for e in current:
        key = (e["end"], e["accn"])
        if key in by_key:
            by_key[key]["val"] += e["val"]
    return list(by_key.values())


async def main():
    print(DIVIDER)
    print("PHASE 34 VERIFICATION: SEC EDGAR foundation")
    print(DIVIDER)

    # 1. Negative case A: ticker with no CIK at all
    print(f"\n[1] Nonexistent ticker '{NONEXISTENT_TICKER}' -> get_cik:")
    cik = await sec_edgar.get_cik(NONEXISTENT_TICKER)
    print(f"    {cik!r} (expected: None)")
    assert cik is None, "Expected None for a nonexistent ticker"

    # 2. Negative case B: real CIK, likely no XBRL companyfacts (20-F filer)
    print(f"\n[2] Foreign filer '{FOREIGN_FILER_TICKER}' (Toyota, files 20-F):")
    cik = await sec_edgar.get_cik(FOREIGN_FILER_TICKER)
    print(f"    CIK: {cik!r}")
    if cik:
        facts = await sec_edgar.fetch_company_facts(cik)
        print(f"    companyfacts result: {'has data' if facts else 'None (no XBRL coverage)'}")
    else:
        print("    No CIK found either -- not in the ticker map at all.")

    # 3. Main run: 5 real companies, full concept history, persist to DB
    print(f"\n[3] Fetching + persisting real concept history for {TEST_TICKERS}:")
    apple_ni_history = None
    async with AsyncSessionLocal() as session:
        for ticker in TEST_TICKERS:
            cik = await sec_edgar.get_cik(ticker)
            if not cik:
                print(f"    {ticker}: no CIK found, skipping")
                continue
            facts = await sec_edgar.fetch_company_facts(cik)
            if not facts:
                print(f"    {ticker}: CIK {cik} found but no XBRL companyfacts, skipping")
                continue

            company = await get_or_create_company(session, ticker)
            total_rows = 0
            for field, candidates in sec_edgar.CONCEPT_CANDIDATES.items():
                history = sec_edgar.extract_concept_history(facts, candidates)
                total_rows += await persist_facts(session, company, field, history)
                if ticker == "AAPL" and field == "net_income":
                    apple_ni_history = history

            debt_history = await fetch_total_debt_history(facts)
            total_rows += await persist_facts(session, company, "total_debt_approx", debt_history)

            print(f"    {ticker} (CIK {cik}): {total_rows} fact rows persisted")

    # 4. Reproduce the known Apple FY2007 restatement from real, freshly-fetched data
    print("\n[4] Apple FY2007 NetIncomeLoss restatement check:")
    if apple_ni_history:
        fy2007_entries = [e for e in apple_ni_history if e["end"] == "2007-09-29" and e["start"] == "2006-10-01"]
        for e in sorted(fy2007_entries, key=lambda x: x["filed"]):
            print(f"    {e['form']:8s} filed {e['filed']}  accn {e['accn']}  val ${e['val']:,}")
        if len(fy2007_entries) >= 2:
            vals = {e["val"] for e in fy2007_entries}
            print(f"    -> {len(fy2007_entries)} distinct filings, {len(vals)} distinct value(s) "
                  f"{'(restatement reproduced)' if len(vals) > 1 else '(no divergence in this run)'}")
        else:
            print(f"    -> Only {len(fy2007_entries)} entry found for this period this run.")
    else:
        print("    Apple net_income history not available this run (see [3] above).")

    print(f"\n{DIVIDER}\nDone.\n{DIVIDER}")


if __name__ == "__main__":
    asyncio.run(main())
