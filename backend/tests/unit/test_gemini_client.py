"""Gemini daily budget persistence (Phase 45 / A-4).

_budget_check_and_increment() opens its own AsyncSessionLocal() internally
(no caller needs to thread a session through) -- these tests replace that
factory with a fake async-context-manager session so no real DB is needed,
matching this suite's established FakeSession convention (test_reaper.py).

Supersedes the old tests/unit/test_gemini_budget.py (Phase 16), which
tested the in-process _daily_state dict directly -- removed in this phase
because it reset on every Render restart, defeating the cap it enforced.
Its still-relevant constant sanity checks are migrated below; the rest
tested a mechanism that no longer exists.
"""
import app.core.ai.gemini_client as gc_module


class _FakeResult:
    def __init__(self, count: int):
        self._count = count

    def scalar_one(self):
        return self._count


class _FakeSession:
    """Stateful stand-in for the real DB row -- count actually accumulates
    across calls, so tests can exercise real "N successive calls" sequences
    without a real DB, the same way the row's count would in production.
    """
    def __init__(self, starting_count: int = 0):
        self.count = starting_count
        self.committed = False
        self.executed_stmt = None

    async def execute(self, stmt):
        self.executed_stmt = stmt
        self.count += 1
        return _FakeResult(self.count)

    async def commit(self):
        self.committed = True

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False


def _patch_session(monkeypatch, starting_count: int = 0) -> _FakeSession:
    fake_session = _FakeSession(starting_count)
    monkeypatch.setattr(gc_module, "AsyncSessionLocal", lambda: fake_session)
    return fake_session


async def test_call_under_budget_returns_true(monkeypatch):
    _patch_session(monkeypatch, starting_count=4)  # next call brings count to 5
    assert await gc_module._budget_check_and_increment() is True


async def test_call_exactly_at_budget_returns_true(monkeypatch):
    # The call that brings count to exactly the budget is the last allowed one.
    _patch_session(monkeypatch, starting_count=gc_module.GEMINI_DAILY_BUDGET - 1)
    assert await gc_module._budget_check_and_increment() is True


async def test_call_over_budget_returns_false(monkeypatch):
    _patch_session(monkeypatch, starting_count=gc_module.GEMINI_DAILY_BUDGET)
    assert await gc_module._budget_check_and_increment() is False


async def test_session_is_committed_so_the_increment_persists(monkeypatch):
    fake_session = _patch_session(monkeypatch)
    await gc_module._budget_check_and_increment()
    assert fake_session.committed is True


async def test_successive_calls_allow_exactly_the_budget_then_reject(monkeypatch):
    fake_session = _patch_session(monkeypatch)
    for _ in range(gc_module.GEMINI_DAILY_BUDGET):
        assert await gc_module._budget_check_and_increment() is True
    # One call beyond the limit
    assert await gc_module._budget_check_and_increment() is False


async def test_a_second_call_in_the_same_process_still_checks_the_db(monkeypatch):
    # Regression guard for the bug this phase fixes: the old in-process dict
    # let every call after the first skip straight to an in-memory check.
    # Here every call must go through the fake session, proving there's no
    # in-memory shortcut left.
    fake_session = _patch_session(monkeypatch, starting_count=gc_module.GEMINI_DAILY_BUDGET)
    await gc_module._budget_check_and_increment()
    first_call_count = fake_session.count
    await gc_module._budget_check_and_increment()
    assert fake_session.count == first_call_count + 1


def test_budget_constant_is_conservative():
    # Must be positive and well under Gemini's 1,500 req/day free-tier limit.
    assert 0 < gc_module.GEMINI_DAILY_BUDGET <= 500


def test_timeout_constant_is_positive():
    assert gc_module.GEMINI_CALL_TIMEOUT_SECONDS > 0
