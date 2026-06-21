"""Restatement Detector (Phase 35).

Compares every value SEC EDGAR has on record for the same (concept, period)
against each other, looking for a figure that changed between filings. Does
NOT fit BaseForensicModule -- that interface analyzes one List[FinancialData]
time series; this compares multiple filed values for the same period against
each other. Flag-only per the 2026-06-21 owner decision (MASTER_IMPLEMENTATION_
PLAN.md Phase 35) -- no score, no fraud_scorer.py weight, just RedFlagData.

Two tiers, because magnitude alone cannot separate fraud-relevant restatements
from benign reclassifications (confirmed against real data during scoping --
MSFT's likely 2017 tax-adjustment and JPM's likely cash-flow reclassification
are both large, neither is a known fraud case):

  Tier 1 (high confidence): the revising filing is a formal SEC amendment
  (form_type ending "/A" -- 10-K/A, 10-Q/A). This is SEC's own mechanism for
  "I am correcting a previously filed report," a real regulatory action.
  Flagged regardless of size; severity scales with size.

  Tier 2 (lower confidence): no amendment filing, but the first-ever-filed
  value and the most-recent-filed value diverge by more than
  TIER2_DIVERGENCE_THRESHOLD. Only fires when Tier 1 didn't already explain
  the period (avoids a redundant second flag for the same underlying event).

Deduplication is structural, not a separate step: each (concept, period_start,
period_end) group produces at most one flag, regardless of how many later
filings echo an already-corrected value forward as a comparative figure.
"""
from app.core.forensics.base import RedFlagData
from app.models.edgar_fact import EdgarFinancialFact

# Below this, divergence is noise (rounding, presentation) per real data
# reviewed during Phase 35 scoping -- TSLA's revenue figures showed
# 0.001-0.01% drift that's clearly just rounding-to-the-nearest-million in
# later comparative tables, not a restatement.
TIER2_DIVERGENCE_THRESHOLD = 0.10


def detect_restatements(facts: list[EdgarFinancialFact]) -> list[RedFlagData]:
    groups: dict[tuple[str, str, str], list[EdgarFinancialFact]] = {}
    for f in facts:
        key = (f.concept, f.period_start, f.period_end)
        groups.setdefault(key, []).append(f)

    flags = []
    for (concept, period_start, period_end), rows in groups.items():
        if len({r.value for r in rows}) < 2:
            continue  # value never changed across filings -- nothing to detect

        ordered = sorted(rows, key=lambda r: (r.filed_date, r.accession_number))

        flag = _find_tier1_amendment(ordered, concept, period_end)
        if flag is None:
            flag = _check_tier2_drift(ordered, concept, period_end)
        if flag is not None:
            flags.append(flag)

    return flags


def _find_tier1_amendment(ordered: list[EdgarFinancialFact], concept: str, period_end: str) -> RedFlagData | None:
    for prev, curr in zip(ordered, ordered[1:]):
        if curr.value != prev.value and curr.form_type.endswith("/A"):
            pct = _relative_divergence(prev.value, curr.value)
            return RedFlagData(
                flag_type="restatement",
                severity=_tier1_severity(pct),
                description=(
                    f"{concept} for the period ending {period_end} was amended: "
                    f"{prev.form_type} (filed {prev.filed_date}) reported {prev.value:,.0f}, "
                    f"{curr.form_type} (filed {curr.filed_date}) reported {curr.value:,.0f} "
                    f"({pct:.1%} change)."
                ),
                period=period_end,
            )
    return None


def _check_tier2_drift(ordered: list[EdgarFinancialFact], concept: str, period_end: str) -> RedFlagData | None:
    first, last = ordered[0], ordered[-1]
    if first.value == last.value:
        return None
    pct = _relative_divergence(first.value, last.value)
    if pct < TIER2_DIVERGENCE_THRESHOLD:
        return None
    return RedFlagData(
        flag_type="restatement",
        severity="high" if pct >= 0.30 else "moderate",
        description=(
            f"{concept} for the period ending {period_end} was reported differently in a "
            f"later filing, with no formal amendment on record: {first.form_type} "
            f"(filed {first.filed_date}) reported {first.value:,.0f}, {last.form_type} "
            f"(filed {last.filed_date}) reported {last.value:,.0f} ({pct:.1%} change). "
            f"May reflect a routine reclassification rather than a restatement -- treat "
            f"with more caution than a formally amended filing."
        ),
        period=period_end,
    )


def _relative_divergence(a: float, b: float) -> float:
    if a == 0:
        return float("inf") if b != 0 else 0.0
    return abs(b - a) / abs(a)


def _tier1_severity(pct: float) -> str:
    if pct >= 0.30:
        return "severe"
    if pct >= 0.05:
        return "high"
    return "moderate"
