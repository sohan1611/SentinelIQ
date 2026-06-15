"""Historical backtest: Wirecard AG (FY2016-FY2018).

Exercises ForensicsRunner + FraudScorer against Wirecard's last three "clean"
annual reports before the scandal became public in early 2019 (the FY2018
annual report was the last one published before Wirecard's auditor refused to
sign off on FY2019, leading to the June 2020 insolvency).

Data provenance
----------------
- Revenue (EUR millions): 2016=1,020; 2017=1,489; 2018=2,016 -- as reported in
  Wirecard's FY2016-FY2018 annual reports.
- Net income (EUR millions): 2018=347 -- as reported (FY2018 annual report).
  2016/2017 net income (210/280) are reconstructed from reported EBITDA
  (EUR 307M / EUR 410M) at a plausible EBITDA-to-net-income conversion ratio;
  not independently re-verified against the full income statement.
- Total assets (EUR millions): 2018=5,855 -- as reported. 2016/2017
  (2,700/4,800) are reconstructed to reflect the well-documented step change
  driven by the 2017 Citi Prepaid Card Services (North America) acquisition.
- Accounts receivable, total debt, operating cash flow, and gross margin are
  illustrative approximations chosen to reflect two specific, widely reported
  patterns from the post-collapse investigation and pre-collapse short-seller
  reports (FT "House of Wirecard" series, 2019; KPMG special audit, 2020):
    1. Receivables ballooning from ~54% to ~94% of annual revenue -- echoing
       the ~EUR 1.9bn in "trustee account" balances with third-party
       acquiring (TPA) partners that KPMG could not verify.
    2. Total debt growing 6x in 2017 (EUR 200M -> EUR 1,200M) to fund the
       Citi NA acquisition, with operating cash flow that never recovered to
       a healthy multiple of that debt -- the debt-funded-acquisition stress
       pattern flagged by debt_analysis below.
  These are illustrative, not exact filed figures.

Expected findings (see Phase 4 completion report for full discussion)
-----------------------------------------------------------------------
- revenue_quality scores SEVERE (<=20) with a HIGH-severity flag for "Revenue
  growing significantly faster than cash flow", driven by both the
  operating-cash-flow divergence and the >10%/year receivables-ratio jump.
- debt_stress scores HIGH-risk territory (<=40), driven by the 2017
  acquisition-debt spike and persistently weak interest coverage.
- cashflow_integrity and earnings_quality read CLEAN (~90-100) on these
  figures -- a DOCUMENTED LIMITATION: none of the four current forensic
  modules directly examine balance-sheet COMPOSITION (e.g. receivables or
  cash as a share of total assets), which is where Wirecard's core fraud
  (fictitious cash/receivables) actually lived.
- The OVERALL integrity_score lands at exactly 60.0 -- "moderate risk", the
  worst score the current weighting allows before crossing into "high" --
  see the ADR-011 gap discussion in the Phase 4 report.

Run from backend/: .venv\\Scripts\\python.exe scripts\\backtest_wirecard.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.models.financial_data import FinancialData
from app.core.forensics.forensics_runner import ForensicsRunner
from app.core.scoring.fraud_scorer import FraudScorer


def build_dataset() -> list[FinancialData]:
    return [
        FinancialData(
            period="2016", period_type="annual",
            revenue=1020.0, net_income=210.0, operating_cf=80.0, free_cf=40.0,
            total_debt=200.0, total_assets=2700.0, accounts_recv=550.0, gross_margin=0.55,
        ),
        FinancialData(
            period="2017", period_type="annual",
            revenue=1489.0, net_income=280.0, operating_cf=70.0, free_cf=20.0,
            total_debt=1200.0, total_assets=4800.0, accounts_recv=1100.0, gross_margin=0.56,
        ),
        FinancialData(
            period="2018", period_type="annual",
            revenue=2016.0, net_income=347.0, operating_cf=50.0, free_cf=0.0,
            total_debt=1700.0, total_assets=5855.0, accounts_recv=1900.0, gross_margin=0.58,
        ),
    ]


def main():
    data = build_dataset()
    forensics = ForensicsRunner().run_forensics(data)

    revenue, cashflow, earnings, debt = (
        forensics["revenue"], forensics["cashflow"], forensics["earnings"], forensics["debt"],
    )

    # Mirrors analysis_worker._stage_forensics's mapping onto FraudScorer's
    # weight-vector keys (governance/narrative/news are out of scope for a
    # pure financial-statement backtest, so they are absent here and
    # correctly excluded by the Phase 3 renormalization rather than diluted
    # with a neutral 50.0).
    scores = {
        "financial": (revenue.score + debt.score) / 2,
        "cashflow": cashflow.score,
        "earnings": earnings.score,
    }
    integrity_score, confidence = FraudScorer().compute_integrity_score(scores, period_count=len(data))
    risk = FraudScorer().classify_risk(integrity_score)

    print("=" * 60)
    print("WIRECARD AG -- FY2016-FY2018 backtest")
    print("=" * 60)
    print(f"revenue_quality   : score={revenue.score:5.1f}  flags={[f.severity for f in revenue.flags]}")
    print(f"cashflow_integrity: score={cashflow.score:5.1f}  flags={[f.severity for f in cashflow.flags]}")
    print(f"earnings_quality  : score={earnings.score:5.1f}  flags={[f.severity for f in earnings.flags]}")
    print(f"debt_stress       : score={debt.score:5.1f}  flags={[f.severity for f in debt.flags]}")
    print("-" * 60)
    print(f"scores (financial/cashflow/earnings): {scores}")
    print(f"integrity_score={integrity_score}  confidence={confidence}  risk={risk.upper()}")
    print("=" * 60)

    # --- Pinned findings -------------------------------------------------
    # 1. revenue_quality independently classifies Wirecard as SEVERE risk,
    #    driven by both the OCF divergence and the receivables-ratio jump
    #    (the closest the current engine gets to the "missing EUR 1.9bn"
    #    receivables story).
    assert revenue.score <= 20.0, f"expected revenue_quality <= 20 (severe), got {revenue.score}"
    assert any(f.severity == "high" for f in revenue.flags), "expected a HIGH revenue-quality flag"

    # 2. debt_stress independently classifies the 2017 acquisition-debt spike
    #    as HIGH risk.
    assert debt.score <= 40.0, f"expected debt_stress <= 40 (high), got {debt.score}"

    # 3. Documented gap (ADR-011): cashflow_integrity and earnings_quality
    #    read clean -- neither examines balance-sheet composition, which is
    #    where the fictitious cash/receivables actually lived.
    assert cashflow.score >= 80.0
    assert earnings.score >= 80.0

    # 4. Overall classification: "moderate risk" -- the worst score the
    #    current weighting allows (3-of-5 modules available, financial =
    #    avg(revenue, debt)) before crossing into "high". Two of four
    #    forensic modules independently flag SEVERE/HIGH; the blended score
    #    sits exactly at the moderate/high boundary. See the Phase 4 report.
    assert integrity_score == 60.0
    assert risk == "moderate"
    assert confidence == "medium"

    print("\nAll pinned findings verified.")


if __name__ == "__main__":
    main()
