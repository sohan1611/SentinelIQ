from pathlib import Path
from app.core.ai.gemini_client import generate_json_with_provenance
from app.models.red_flag import RedFlag

class GovernanceScorer:
    async def analyze(self, company_name: str, news_text: str) -> tuple[float, list[dict], dict]:
        prompt_path = Path(__file__).parent.parent / "ai" / "prompts" / "governance_prompt.txt"
        with open(prompt_path, "r", encoding="utf-8") as f:
            prompt_template = f.read()

        prompt = prompt_template.format(company_name=company_name, news_text=news_text)

        events, provenance = await generate_json_with_provenance(prompt)
        provenance_record = {
            "model_id": provenance["model_id"],
            "prompt": provenance["prompt"],
            "raw_response": provenance["raw_response"],
        }

        if events is None:
            return 50.0, [], provenance_record

        if not isinstance(events, list):
            events = []

        score = 100.0
        flags = []

        for event in events:
            severity = event.get("severity", "moderate")
            if severity == "moderate":
                score -= 15
            elif severity == "high":
                score -= 25
            elif severity == "severe":
                score -= 35

            event_date_approx = event.get("event_date_approx")
            flags.append({
                "flag_type": "governance",
                "severity": severity,
                "description": event.get("description", "Governance event detected"),
                "period": event_date_approx[:20] if event_date_approx else None
            })

        score = max(0.0, min(100.0, score))
        return score, flags, provenance_record
