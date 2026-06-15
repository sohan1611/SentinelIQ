"""Historical backtest: Enron Corporation (FY1997-FY2000).

Exercises ForensicsRunner + FraudScorer against Enron's AS-REPORTED financial
statement line items for the four fiscal years immediately preceding its
December 2001 bankruptcy -- the same figures a forensic analyst would have had
access to in real time, before the November 2001 restatement.

Data provenance
----------------
- Revenue (USD millions): 1997=20,300; 1998=31,260; 1999=40,112; 2000=100,789.
  1998-2000 figures are as reported in Enron's FY1999 and FY2000 Form 10-K
  filings (SEC EDGAR). The 1999->2000 jump of +151% was driven almost
  entirely by gross (notional) revenue recognition on energy-trading
  contracts under EITF 98-10 mark-to-market accounting -- the single most
  cited "too good to be true" figure in Enron's history.
- Net income (USD millions): 1997=105 (depressed by ~$463M of special charges
  related to JEDI/Chewco); 1998=703; 1999=893; 2000=979. Net income grew only
  ~40% over 1998-2000 while revenue grew >220% -- a textbook
  revenue/profitability divergence.
- Operating cash flow, total debt, total assets, accounts receivable, and
  gross margin are reconstructed to the documented ORDER OF MAGNITUDE and
  DIRECTION (slow-growing OCF, steadily rising on-balance-sheet debt, rising
  receivables, declining gross margin as trading revenue diluted the mix) but
  are illustrative approximations, not exact filed figures -- precise
  cash-flow-statement and balance-sheet line items were not independently
  re-verified against the full 10-K text for this backtest.

Expected findings (see Phase 4 completion report for full discussion)
-----------------------------------------------------------------------
- revenue_quality scores SEVERE (<=20) with a HIGH-severity flag for "Revenue
  growing significantly faster than cash flow" -- the engine correctly
  reproduces the mark-to-market revenue-recognition critique.
- cashflow_integrity and debt_analysis score CLEAN (~100) on these
  AS-REPORTED figures. This is a DOCUMENTED, KNOWN LIMITATION, not a test
  bug: Enron's fraud was substantially in (a) gross revenue recognition and
  (b) off-balance-sheet debt via Special Purpose Entities that never appear
  in `total_debt` on the parent's reported balance sheet -- neither of which
  the Sloan accrual ratio or a reported-debt-to-revenue ratio can see.
- The OVERALL integrity_score lands in "low risk" (61-80), NOT "high"/
  "severe" -- see the ADR-011 gap discussion in the Phase 4 report.

Run from backend/: .venv\\Scripts\\python.exe scripts\\backtest_enron.py
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
            period="1997", period_type="annual",
            revenue=20300.0, net_income=105.0, operating_cf=1500.0, free_cf=1200.0,
            total_debt=6500.0, total_assets=23200.0, accounts_recv=2000.0, gross_margin=0.15,
        ),
        FinancialData(
            period="1998", period_type="annual",
            revenue=31260.0, net_income=703.0, operating_cf=1650.0, free_cf=1300.0,
            total_debt=7357.0, total_assets=29350.0, accounts_recv=2186.0, gross_margin=0.10,
        ),
        FinancialData(
            period="1999", period_type="annual",
            revenue=40112.0, net_income=893.0, operating_cf=1630.0, free_cf=1250.0,
            total_debt=8152.0, total_assets=33381.0, accounts_recv=3030.0, gross_margin=0.09,
        ),
        FinancialData(
            period="2000", period_type="annual",
            revenue=100789.0, net_income=979.0, operating_cf=2000.0, free_cf=1500.0,
            total_debt=10229.0, total_assets=65503.0, accounts_recv=10396.0, gross_margin=0.04,
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
    print("ENRON CORPORATION -- FY1997-FY2000 backtest")
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
    # 1. revenue_quality independently classifies Enron as SEVERE risk.
    assert revenue.score <= 20.0, f"expected revenue_quality <= 20 (severe), got {revenue.score}"
    assert any(f.severity == "high" for f in revenue.flags), "expected a HIGH revenue-quality flag"
    assert any("faster than cash flow" in f.description for f in revenue.flags)

    # 2. Documented gap (ADR-011): cashflow_integrity and debt_analysis read
    #    clean on as-reported figures -- Enron's fraud lived in gross revenue
    #    recognition and off-balance-sheet SPE debt, neither visible to these
    #    ratios. This assertion documents the gap rather than hiding it.
    assert cashflow.score >= 80.0
    assert debt.score >= 80.0

    # 3. Overall classification: "low risk" (61-80) -- the severe
    #    revenue-quality signal pulls the blended score down to the worst
    #    band the current weighting allows when only the 3-of-5 financial
    #    statement modules carry signal. See the Phase 4 report.
    assert 60.0 < integrity_score <= 80.0, (
        f"expected integrity_score in (60, 80] (low risk) given current "
        f"weights/modules, got {integrity_score} ({risk})"
    )
    assert risk == "low"
    assert confidence == "medium"

    print("\nAll pinned findings verified.")


if __name__ == "__main__":
    main()
