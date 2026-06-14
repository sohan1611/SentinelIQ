from pathlib import Path
from typing import List, Dict
from app.core.ai.gemini_client import generate_json_with_provenance

class ConsistencyEngine:
    async def analyze(self, company_name: str, statements: List[Dict[str, str]]) -> tuple[float, list[dict], list[dict], list[dict]]:
        prompt_path = Path(__file__).parent.parent / "ai" / "prompts" / "narrative_prompt.txt"
        with open(prompt_path, "r", encoding="utf-8") as f:
            prompt_template = f.read()

        snapshots = []
        provenance_records = []
        for stmt in statements:
            period = stmt["period"]
            text = stmt["text"]
            source = stmt["source"]

            prompt = prompt_template.format(company_name=company_name, period=period, statement_text=text)
            result, provenance = await generate_json_with_provenance(prompt)
            provenance_records.append({
                "period": period,
                "model_id": provenance["model_id"],
                "prompt": provenance["prompt"],
                "raw_response": provenance["raw_response"],
            })

            if result is None:
                continue

            snapshots.append({
                "period": period,
                "statement_text": text,
                "sentiment_label": result.get("sentiment_label", "neutral"),
                "sentiment_score": float(result.get("sentiment_score", 0.0)),
                "source": source
            })

        if len(snapshots) < 2:
            return 50.0, snapshots, [], provenance_records

        snapshots = sorted(snapshots, key=lambda x: x["period"])

        contradictions = []
        contradiction_scores = []

        for i in range(1, len(snapshots)):
            prev = snapshots[i-1]
            curr = snapshots[i]

            diff = abs(curr["sentiment_score"] - prev["sentiment_score"])
            contradiction_scores.append(diff)

            if diff > 0.6:
                contradictions.append({
                    "flag_type": "narrative",
                    "severity": "high" if diff > 0.8 else "moderate",
                    "description": f"Significant tone shift between {prev['period']} and {curr['period']} (Score diff: {diff:.2f})",
                    "period": curr["period"]
                })

        if not contradiction_scores:
            return 50.0, snapshots, contradictions, provenance_records

        avg_contradiction = sum(contradiction_scores) / len(contradiction_scores)
        narrative_score = max(0.0, 100.0 - (avg_contradiction * 100.0))

        return narrative_score, snapshots, contradictions, provenance_records
