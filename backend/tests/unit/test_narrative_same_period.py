from unittest.mock import AsyncMock, patch

from app.core.narrative.consistency_engine import ConsistencyEngine


async def test_same_period_sentiment_gap_returns_neutral_score_without_contradiction():
    statements = [
        {
            "period": "2026-08-10",
            "text": "Acme reported record revenue and strong demand.",
            "source": "test",
        },
        {
            "period": "2026-08-10",
            "text": "Acme warned investors about a liquidity crisis.",
            "source": "test",
        },
    ]
    provenance = {
        "model_id": "test-model",
        "prompt": "test prompt",
        "raw_response": "test response",
    }

    with patch(
        "app.core.narrative.consistency_engine.generate_json_with_provenance",
        new_callable=AsyncMock,
    ) as mock_generate:
        mock_generate.side_effect = [
            (
                {
                    "sentiment_label": "positive",
                    "sentiment_score": 0.9,
                    "source_quote": "record revenue",
                },
                provenance,
            ),
            (
                {
                    "sentiment_label": "negative",
                    "sentiment_score": -0.9,
                    "source_quote": "liquidity crisis",
                },
                provenance,
            ),
        ]

        score, _, contradictions, _ = await ConsistencyEngine().analyze(
            "Acme Corp", statements
        )

    assert score == 50.0
    assert contradictions == []


async def test_distinct_period_sentiment_gap_creates_contradiction():
    statements = [
        {
            "period": "2026-08-09",
            "text": "Acme reported record revenue and strong demand.",
            "source": "test",
        },
        {
            "period": "2026-08-10",
            "text": "Acme warned investors about a liquidity crisis.",
            "source": "test",
        },
    ]
    provenance = {
        "model_id": "test-model",
        "prompt": "test prompt",
        "raw_response": "test response",
    }

    with patch(
        "app.core.narrative.consistency_engine.generate_json_with_provenance",
        new_callable=AsyncMock,
    ) as mock_generate:
        mock_generate.side_effect = [
            (
                {
                    "sentiment_label": "positive",
                    "sentiment_score": 0.9,
                    "source_quote": "record revenue",
                },
                provenance,
            ),
            (
                {
                    "sentiment_label": "negative",
                    "sentiment_score": -0.9,
                    "source_quote": "liquidity crisis",
                },
                provenance,
            ),
        ]

        _, _, contradictions, _ = await ConsistencyEngine().analyze(
            "Acme Corp", statements
        )

    assert len(contradictions) == 1
    assert "2026-08-09" in contradictions[0]["description"]
    assert "2026-08-10" in contradictions[0]["description"]
