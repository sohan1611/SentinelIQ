# Phase 3 (2026-06-14, ADR-005/006): narrative excluded from the weight vector until
# it carries real signal; remaining 5 modules renormalized from 0.90 -> 1.0.
# See CLAUDE.md "Fraud Score Weights" for the full amendment.
BASE_WEIGHTS: dict[str, float] = {
    "financial": 0.3333,
    "cashflow": 0.2222,
    "governance": 0.1667,
    "earnings": 0.1667,
    "news": 0.1111,
}


class FraudScorer:
    def compute_integrity_score(self, scores: dict, period_count: int = 0) -> tuple[float, str]:
        available = {k: v for k, v in scores.items() if k in BASE_WEIGHTS and v is not None}
        if not available:
            return 50.0, "low"

        total_weight = sum(BASE_WEIGHTS[k] for k in available)
        weighted_sum = sum(BASE_WEIGHTS[k] * v for k, v in available.items())
        integrity_score = round(weighted_sum / total_weight, 1)

        confidence = self._confidence_tier(len(available), len(BASE_WEIGHTS), period_count)
        return integrity_score, confidence

    def _confidence_tier(self, available_count: int, total_count: int, period_count: int) -> str:
        if available_count <= 2:
            return "low"
        if available_count == total_count and period_count >= 3:
            return "high"
        return "medium"

    def classify_risk(self, score: float) -> str:
        if score <= 20: return "severe"
        if score <= 40: return "high"
        if score <= 60: return "moderate"
        if score <= 80: return "low"
        return "strong"
