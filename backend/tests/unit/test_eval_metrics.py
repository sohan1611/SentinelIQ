"""Unit tests for the precision/recall/FPR calculator (Phase 43 / H-5)."""
from app.core.forensics.eval_metrics import compute_classification_metrics, DEFAULT_THRESHOLD


def test_perfect_classifier():
    results = [
        {"ticker": "FRAUD1", "label": "fraud", "integrity_score": 20.0},
        {"ticker": "FRAUD2", "label": "fraud", "integrity_score": 35.0},
        {"ticker": "CLEAN1", "label": "clean", "integrity_score": 85.0},
        {"ticker": "CLEAN2", "label": "clean", "integrity_score": 90.0},
    ]
    m = compute_classification_metrics(results)
    assert m["true_positives"] == 2
    assert m["false_positives"] == 0
    assert m["true_negatives"] == 2
    assert m["false_negatives"] == 0
    assert m["precision"] == 1.0
    assert m["recall"] == 1.0
    assert m["false_positive_rate"] == 0.0


def test_worst_case_classifier_flags_everything():
    results = [
        {"ticker": "FRAUD1", "label": "fraud", "integrity_score": 10.0},
        {"ticker": "CLEAN1", "label": "clean", "integrity_score": 30.0},
        {"ticker": "CLEAN2", "label": "clean", "integrity_score": 40.0},
    ]
    m = compute_classification_metrics(results)
    assert m["true_positives"] == 1
    assert m["false_positives"] == 2
    assert m["recall"] == 1.0
    assert m["false_positive_rate"] == 1.0
    assert m["precision"] == 1 / 3


def test_nothing_flagged_gives_zero_recall_and_zero_fpr_not_crash():
    results = [
        {"ticker": "FRAUD1", "label": "fraud", "integrity_score": 95.0},
        {"ticker": "CLEAN1", "label": "clean", "integrity_score": 90.0},
    ]
    m = compute_classification_metrics(results)
    assert m["true_positives"] == 0
    assert m["false_positives"] == 0
    assert m["recall"] == 0.0
    assert m["false_positive_rate"] == 0.0
    # precision is undefined (0/0), not fabricated as 0.0 or 1.0
    assert m["precision"] is None


def test_none_score_excluded_and_reported_as_unscored_not_a_negative():
    results = [
        {"ticker": "NOCOVERAGE", "label": "fraud", "integrity_score": None},
        {"ticker": "CLEAN1", "label": "clean", "integrity_score": 85.0},
    ]
    m = compute_classification_metrics(results)
    assert m["unscored"] == ["NOCOVERAGE"]
    # The unscored fraud case must not silently count as a false negative --
    # absence of signal is not the same claim as "the model said clean".
    assert m["false_negatives"] == 0
    assert m["true_negatives"] == 1


def test_score_exactly_at_threshold_counts_as_flagged():
    results = [{"ticker": "X", "label": "fraud", "integrity_score": DEFAULT_THRESHOLD}]
    m = compute_classification_metrics(results)
    assert m["true_positives"] == 1


def test_empty_results_returns_zeros_not_crash():
    m = compute_classification_metrics([])
    assert m["true_positives"] == 0
    assert m["precision"] is None
    assert m["recall"] is None
    assert m["false_positive_rate"] is None
    assert m["unscored"] == []


def test_custom_threshold_is_respected():
    results = [{"ticker": "X", "label": "fraud", "integrity_score": 45.0}]
    assert compute_classification_metrics(results, threshold=40.0)["true_positives"] == 0
    assert compute_classification_metrics(results, threshold=50.0)["true_positives"] == 1


def test_no_min_confidence_counts_everything_unchanged():
    # Default behavior (min_confidence=None) must stay exactly as before --
    # existing callers that never pass confidence keep working.
    results = [{"ticker": "X", "label": "clean", "integrity_score": 85.0}]
    m = compute_classification_metrics(results)
    assert m["low_confidence_excluded"] == []
    assert m["true_negatives"] == 1


def test_low_confidence_result_excluded_not_counted_as_real_negative():
    # A score of 50.0 produced by infrastructure failure (rate-limited
    # yfinance/Gemini) would otherwise count as a FALSE POSITIVE here (50 is
    # <= the default 60 threshold) despite carrying no real signal --
    # confidence is what tells it apart from a genuine finding (Phase 43
    # Step 3, found live).
    results = [
        {"ticker": "DEGRADED", "label": "clean", "integrity_score": 50.0, "confidence": "low"},
        {"ticker": "REAL", "label": "clean", "integrity_score": 85.0, "confidence": "high"},
    ]
    m = compute_classification_metrics(results, min_confidence="medium")
    assert m["low_confidence_excluded"] == ["DEGRADED"]
    assert m["true_negatives"] == 1
    assert m["false_positives"] == 0


def test_missing_confidence_treated_as_below_any_filter():
    # A result with no confidence key at all (e.g. an older corpus entry)
    # must not silently pass a min_confidence filter -- missing confidence
    # is treated as below any real tier, same "absence is not neutral"
    # principle as the None-score handling above.
    results = [{"ticker": "X", "label": "fraud", "integrity_score": 20.0}]
    m = compute_classification_metrics(results, min_confidence="low")
    assert m["low_confidence_excluded"] == ["X"]
    assert m["true_positives"] == 0


def test_min_confidence_low_admits_low_medium_and_high():
    results = [
        {"ticker": "A", "label": "fraud", "integrity_score": 20.0, "confidence": "low"},
        {"ticker": "B", "label": "fraud", "integrity_score": 20.0, "confidence": "medium"},
        {"ticker": "C", "label": "fraud", "integrity_score": 20.0, "confidence": "high"},
    ]
    m = compute_classification_metrics(results, min_confidence="low")
    assert m["low_confidence_excluded"] == []
    assert m["true_positives"] == 3
