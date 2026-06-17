"""Unit tests for GovernanceEvent schema validation (M-5).

Verifies that malformed severity values, missing descriptions, and unknown
fields are all handled gracefully before any scoring logic runs.
"""
import pytest
from pydantic import ValidationError

from app.core.governance.governance_scorer import GovernanceEvent


def test_valid_moderate_event_passes_through():
    event = GovernanceEvent.model_validate({
        "severity": "moderate",
        "description": "CFO resigned unexpectedly",
        "event_type": "executive_departure",
        "event_date_approx": "2024-01-15",
    })
    assert event.severity == "moderate"
    assert event.description == "CFO resigned unexpectedly"
    assert event.event_type == "executive_departure"
    assert event.event_date_approx == "2024-01-15"


def test_valid_high_severity():
    event = GovernanceEvent.model_validate({"severity": "high", "description": "SEC investigation"})
    assert event.severity == "high"


def test_valid_severe_severity():
    event = GovernanceEvent.model_validate({"severity": "severe", "description": "Auditor resigned"})
    assert event.severity == "severe"


def test_unknown_severity_normalizes_to_moderate():
    # A parseable-but-malformed severity must still produce a deduction (M-5).
    event = GovernanceEvent.model_validate({"severity": "kinda bad", "description": "Some event"})
    assert event.severity == "moderate"


def test_severity_case_insensitive():
    for raw, expected in [("HIGH", "high"), ("Severe", "severe"), ("MODERATE", "moderate")]:
        event = GovernanceEvent.model_validate({"severity": raw, "description": "Event"})
        assert event.severity == expected


def test_empty_description_defaults():
    event = GovernanceEvent.model_validate({"severity": "moderate", "description": ""})
    assert event.description == "Governance event detected"


def test_whitespace_only_description_defaults():
    event = GovernanceEvent.model_validate({"severity": "high", "description": "   "})
    assert event.description == "Governance event detected"


def test_missing_optional_fields_default_to_none():
    event = GovernanceEvent.model_validate({"severity": "moderate", "description": "Event"})
    assert event.event_type is None
    assert event.event_date_approx is None


def test_extra_fields_are_ignored():
    event = GovernanceEvent.model_validate({
        "severity": "high",
        "description": "Event",
        "unexpected_field": "should be ignored",
    })
    assert event.severity == "high"
