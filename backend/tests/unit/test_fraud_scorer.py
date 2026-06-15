import pytest

from app.core.scoring.fraud_scorer import BASE_WEIGHTS, FraudScorer


@pytest.fixture
def scorer():
    return FraudScorer()


def test_base_weights_sum_to_one_and_exclude_narrative():
    assert sum(BASE_WEIGHTS.values()) == pytest.approx(1.0)
    assert "narrative" not in BASE_WEIGHTS


def test_all_five_modules_present_with_enough_periods_is_high_confidence(scorer):
    scores = {
        "financial": 90, "cashflow": 80, "governance": 70,
        "earnings": 60, "news": 50, "narrative": 999,
    }

    integrity_score, confidence = scorer.compute_integrity_score(scores, period_count=3)

    assert integrity_score == 75.0
    assert confidence == "high"


def test_all_five_modules_present_with_too_few_periods_is_medium_confidence(scorer):
    scores = {
        "financial": 90, "cashflow": 80, "governance": 70,
        "earnings": 60, "news": 50, "narrative": 999,
    }

    integrity_score, confidence = scorer.compute_integrity_score(scores, period_count=2)

    assert integrity_score == 75.0
    assert confidence == "medium"


def test_one_missing_module_is_renormalized_and_medium_confidence(scorer):
    scores = {
        "financial": None, "cashflow": 80, "governance": 70,
        "earnings": 60, "news": 50, "narrative": 999,
    }

    integrity_score, confidence = scorer.compute_integrity_score(scores, period_count=3)

    # Renormalized over the remaining 4 weights (cashflow+governance+earnings+news
    # = 0.6667): (0.2222*80 + 0.1667*70 + 0.1667*60 + 0.1111*50) / 0.6667 = 67.5
    assert integrity_score == 67.5
    assert confidence == "medium"


def test_two_available_modules_is_low_confidence(scorer):
    scores = {
        "financial": 100, "cashflow": 0, "governance": None,
        "earnings": None, "news": None, "narrative": 50,
    }

    integrity_score, confidence = scorer.compute_integrity_score(scores, period_count=5)

    # Renormalized over financial+cashflow (0.5555): (0.3333*100 + 0.2222*0) / 0.5555 = 60.0
    assert integrity_score == 60.0
    assert confidence == "low"


def test_all_modules_none_returns_neutral_low_confidence(scorer):
    scores = {
        "financial": None, "cashflow": None, "governance": None,
        "earnings": None, "news": None, "narrative": None,
    }

    integrity_score, confidence = scorer.compute_integrity_score(scores, period_count=0)

    assert integrity_score == 50.0
    assert confidence == "low"


def test_narrative_value_never_affects_integrity_score(scorer):
    base_scores = {"financial": 90, "cashflow": 80, "governance": 70, "earnings": 60, "news": 50}

    without_narrative = scorer.compute_integrity_score(dict(base_scores), period_count=3)
    with_narrative = scorer.compute_integrity_score({**base_scores, "narrative": 0.0}, period_count=3)

    assert with_narrative == without_narrative == (75.0, "high")


@pytest.mark.parametrize(
    "score, expected",
    [
        (0, "severe"),
        (20, "severe"),
        (20.1, "high"),
        (40, "high"),
        (40.1, "moderate"),
        (60, "moderate"),
        (60.1, "low"),
        (80, "low"),
        (80.1, "strong"),
        (100, "strong"),
    ],
)
def test_classify_risk_boundaries(scorer, score, expected):
    assert scorer.classify_risk(score) == expected
