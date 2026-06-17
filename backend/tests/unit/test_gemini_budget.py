"""Unit tests for the Gemini daily budget guard (Phase 16).

Verifies: counter increments, budget exhaustion returns False,
counter resets on a new UTC day, and the budget constant is sane.
"""
from datetime import datetime, timedelta, timezone


def _utc_today():
    return datetime.now(timezone.utc).date()


def _reset(module, count=0):
    """Reset budget state to a clean slate (date=None forces a reset on next call)."""
    module._daily_state["date"] = None
    module._daily_state["count"] = count


def test_first_call_is_allowed():
    import app.core.ai.gemini_client as m
    _reset(m)
    assert m._budget_check_and_increment() is True
    assert m._daily_state["count"] == 1


def test_counter_increments_on_each_call():
    import app.core.ai.gemini_client as m
    _reset(m)
    for i in range(1, 5):
        assert m._budget_check_and_increment() is True
        assert m._daily_state["count"] == i


def test_budget_exhausted_returns_false():
    import app.core.ai.gemini_client as m
    _reset(m)
    # Set counter to the limit for today (use UTC date — matches the module)
    m._daily_state["date"] = _utc_today()
    m._daily_state["count"] = m.GEMINI_DAILY_BUDGET

    assert m._budget_check_and_increment() is False
    # Counter must not have incremented past the limit
    assert m._daily_state["count"] == m.GEMINI_DAILY_BUDGET


def test_budget_resets_on_new_day():
    import app.core.ai.gemini_client as m
    # Simulate yesterday's exhausted budget (UTC dates throughout)
    yesterday = _utc_today() - timedelta(days=1)
    m._daily_state["date"] = yesterday
    m._daily_state["count"] = m.GEMINI_DAILY_BUDGET

    # Today's first call should succeed and reset the counter
    assert m._budget_check_and_increment() is True
    assert m._daily_state["count"] == 1
    assert m._daily_state["date"] == _utc_today()


def test_budget_allows_exactly_limit_calls():
    import app.core.ai.gemini_client as m
    _reset(m)

    for _ in range(m.GEMINI_DAILY_BUDGET):
        assert m._budget_check_and_increment() is True

    # One call beyond the limit
    assert m._budget_check_and_increment() is False


def test_budget_constant_is_conservative():
    import app.core.ai.gemini_client as m
    # Must be positive and well under Gemini's 1,500 req/day free-tier limit
    assert 0 < m.GEMINI_DAILY_BUDGET <= 500


def test_timeout_constant_is_positive():
    import app.core.ai.gemini_client as m
    assert m.GEMINI_CALL_TIMEOUT_SECONDS > 0
