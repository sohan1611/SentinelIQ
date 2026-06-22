"""Precision/recall/false-positive-rate calculator for the fraud-signal
validation harness (Phase 43 / H-5). Pure, deterministic -- no network, no
DB. Consumes whatever corpus the orchestration script (Phase 43 Step 2)
produces; the metrics math itself carries no risk of being wrong once
tested here, independent of how representative the corpus turns out to be.
"""

# CLAUDE.md risk band: 41-60 is "moderate risk", <=60 is "moderate risk or
# worse" -- the natural default for "would this score have prompted an
# analyst to look closer". Tunable; not a claim that 60 is the only
# defensible cutoff.
DEFAULT_THRESHOLD = 60.0


_CONFIDENCE_RANK = {"low": 0, "medium": 1, "high": 2}


def compute_classification_metrics(
    results: list[dict], threshold: float = DEFAULT_THRESHOLD, min_confidence: str | None = None
) -> dict:
    """Each result: {"ticker": str, "label": "fraud" | "clean",
    "integrity_score": float | None, "confidence": "low"|"medium"|"high"|None}.

    A score <= threshold counts as "flagged". integrity_score=None (the
    pipeline couldn't score this company at all -- no yfinance/EDGAR
    coverage) is excluded from every count below and reported separately
    as `unscored`, never silently treated as "not flagged" -- that would
    fabricate a negative result from an absence of signal, the same
    "absence is not neutral" principle this codebase applies everywhere
    else (ADR-005).

    min_confidence (optional): when set, a result whose confidence tier is
    BELOW it is also excluded and reported separately as
    `low_confidence_excluded`, not counted as a real TP/FP/TN/FN. A score
    of exactly 50.0 produced by widespread infrastructure failure (e.g.
    yfinance/Gemini rate-limited) is indistinguishable from a genuine
    finding by integrity_score alone -- confidence is what tells them
    apart (Phase 43 Step 3, found live: a real harness run against
    rate-limited yfinance scored several clean companies near 50 purely
    from missing data, which the score-only version of this function
    could not tell apart from a real signal).
    """
    tp = fp = tn = fn = 0
    unscored: list[str] = []
    low_confidence_excluded: list[str] = []

    for r in results:
        score = r.get("integrity_score")
        if score is None:
            unscored.append(r["ticker"])
            continue

        if min_confidence is not None:
            conf = r.get("confidence")
            conf_rank = _CONFIDENCE_RANK.get(conf, -1)  # unknown/missing confidence treated as below any real tier
            if conf_rank < _CONFIDENCE_RANK.get(min_confidence, 0):
                low_confidence_excluded.append(r["ticker"])
                continue

        flagged = score <= threshold
        is_fraud = r["label"] == "fraud"

        if flagged and is_fraud:
            tp += 1
        elif flagged and not is_fraud:
            fp += 1
        elif not flagged and not is_fraud:
            tn += 1
        else:
            fn += 1

    precision = tp / (tp + fp) if (tp + fp) > 0 else None
    recall = tp / (tp + fn) if (tp + fn) > 0 else None
    false_positive_rate = fp / (fp + tn) if (fp + tn) > 0 else None

    return {
        "threshold": threshold,
        "min_confidence": min_confidence,
        "true_positives": tp,
        "false_positives": fp,
        "true_negatives": tn,
        "false_negatives": fn,
        "unscored": unscored,
        "low_confidence_excluded": low_confidence_excluded,
        "precision": precision,
        "recall": recall,
        "false_positive_rate": false_positive_rate,
    }
