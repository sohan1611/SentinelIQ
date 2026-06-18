"""Rate limiter (Phase 18 Step 2): per-IP sliding window enforced on auth + analysis routes.

Tests cover:
- Requests below limit pass without raising
- Breach raises 429 with the standard error envelope
- 429 carries a Retry-After header within the window bounds
- Distinct IPs have independent buckets
- Distinct keys have independent buckets
- X-Forwarded-For is used as the client IP when present
"""
import pytest
from fastapi import HTTPException

from app.api.middleware.rate_limit import rate_limit


class _FakeClient:
    def __init__(self, host: str):
        self.host = host


class _FakeRequest:
    def __init__(self, ip: str, xff: str | None = None):
        self.client = _FakeClient(ip)
        self.headers = {"x-forwarded-for": xff} if xff else {}


async def test_requests_below_limit_pass():
    fn = rate_limit("rl_below", limit=3, window_secs=60)
    req = _FakeRequest("1.2.3.4")
    for _ in range(3):
        await fn(req)  # must not raise


async def test_breach_raises_429():
    fn = rate_limit("rl_breach", limit=2, window_secs=60)
    req = _FakeRequest("1.2.3.5")
    await fn(req)
    await fn(req)

    with pytest.raises(HTTPException) as exc_info:
        await fn(req)

    assert exc_info.value.status_code == 429
    assert exc_info.value.detail["error"]["code"] == "RATE_LIMITED"


async def test_retry_after_header_present_and_bounded():
    fn = rate_limit("rl_header", limit=1, window_secs=60)
    req = _FakeRequest("1.2.3.6")
    await fn(req)  # exhaust the single slot

    with pytest.raises(HTTPException) as exc_info:
        await fn(req)

    assert "Retry-After" in exc_info.value.headers
    retry = int(exc_info.value.headers["Retry-After"])
    assert 1 <= retry <= 60


async def test_distinct_ips_have_independent_buckets():
    fn = rate_limit("rl_ips", limit=1, window_secs=60)
    req_a = _FakeRequest("10.0.0.1")
    req_b = _FakeRequest("10.0.0.2")

    await fn(req_a)  # exhausts limit for 10.0.0.1

    await fn(req_b)  # different IP — must not raise


async def test_distinct_keys_have_independent_buckets():
    req = _FakeRequest("10.0.0.3")
    fn_a = rate_limit("rl_key_a", limit=1, window_secs=60)
    fn_b = rate_limit("rl_key_b", limit=1, window_secs=60)

    await fn_a(req)  # exhausts rl_key_a for this IP

    await fn_b(req)  # different key — must not raise


async def test_xff_header_takes_precedence_over_client_host():
    fn = rate_limit("rl_xff", limit=1, window_secs=60)
    req = _FakeRequest("127.0.0.1", xff="203.0.113.5")
    await fn(req)  # 1st from 203.0.113.5

    with pytest.raises(HTTPException):
        await fn(req)  # 2nd from same XFF IP — rate limited

    req2 = _FakeRequest("127.0.0.1", xff="203.0.113.99")
    await fn(req2)  # different real IP in XFF — must not raise
