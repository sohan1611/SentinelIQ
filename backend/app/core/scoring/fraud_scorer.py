class FraudScorer:
    def compute_integrity_score(self, scores: dict) -> float:
        weighted = (
            scores.get("financial", 50.0) * 0.30 +
            scores.get("cashflow", 50.0) * 0.20 +
            scores.get("governance", 50.0) * 0.15 +
            scores.get("earnings", 50.0) * 0.15 +
            scores.get("narrative", 50.0) * 0.10 +
            scores.get("news", 50.0) * 0.10
        )
        return round(weighted, 1)

    def classify_risk(self, score: float) -> str:
        if score <= 20: return "severe"
        if score <= 40: return "high"
        if score <= 60: return "moderate"
        if score <= 80: return "low"
        return "strong"
