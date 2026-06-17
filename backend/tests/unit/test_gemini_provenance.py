"""Unit tests for _extract_provenance_fields (M-1).

Verifies that the function extracts finish_reason, safety_ratings, and token
counts from a Gemini response object, and returns {} defensively on bad input.
"""
from types import SimpleNamespace

from app.core.ai.gemini_client import _extract_provenance_fields


def _make_response(finish_reason="STOP", safety_ratings=None, prompt_tokens=100, candidates_tokens=50):
    candidate = SimpleNamespace(
        finish_reason=SimpleNamespace(name=finish_reason),
        safety_ratings=safety_ratings or [],
    )
    return SimpleNamespace(
        candidates=[candidate],
        usage_metadata=SimpleNamespace(
            prompt_token_count=prompt_tokens,
            candidates_token_count=candidates_tokens,
        ),
    )


def test_extracts_finish_reason_and_token_counts():
    result = _extract_provenance_fields(_make_response("STOP", prompt_tokens=120, candidates_tokens=40))
    assert result["finish_reason"] == "STOP"
    assert result["prompt_token_count"] == 120
    assert result["candidates_token_count"] == 40
    assert result["safety_ratings"] == []


def test_extracts_safety_ratings():
    rating = SimpleNamespace(
        category=SimpleNamespace(name="HARM_CATEGORY_HARASSMENT"),
        probability=SimpleNamespace(name="NEGLIGIBLE"),
    )
    result = _extract_provenance_fields(_make_response(safety_ratings=[rating]))
    assert result["safety_ratings"] == [
        {"category": "HARM_CATEGORY_HARASSMENT", "probability": "NEGLIGIBLE"}
    ]


def test_no_candidates_produces_none_finish_reason():
    response = SimpleNamespace(
        candidates=[],
        usage_metadata=SimpleNamespace(prompt_token_count=50, candidates_token_count=20),
    )
    result = _extract_provenance_fields(response)
    assert result["finish_reason"] is None
    assert result["safety_ratings"] == []
    assert result["prompt_token_count"] == 50


def test_no_usage_metadata_produces_none_token_counts():
    response = SimpleNamespace(candidates=[], usage_metadata=None)
    result = _extract_provenance_fields(response)
    assert result["prompt_token_count"] is None
    assert result["candidates_token_count"] is None


def test_returns_empty_dict_on_exception():
    class BadResponse:
        @property
        def candidates(self):
            raise RuntimeError("simulated API error")

    result = _extract_provenance_fields(BadResponse())
    assert result == {}


def test_finish_reason_without_name_attr_falls_back_to_str():
    candidate = SimpleNamespace(finish_reason=42, safety_ratings=[])
    response = SimpleNamespace(candidates=[candidate], usage_metadata=None)
    result = _extract_provenance_fields(response)
    assert result["finish_reason"] == "42"
