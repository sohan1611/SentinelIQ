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


async def test_leftmost_xff_entry_is_not_trusted_rightmost_is():
    # H-2: an attacker can put anything they want at the LEFT of their own
    # X-Forwarded-For request header. Only entries appended by our own
    # trusted infrastructure (the rightmost ones) are reliable.
    fn = rate_limit("rl_spoof", limit=1, window_secs=60)

    attacker_attempt_1 = _FakeRequest("127.0.0.1", xff="1.1.1.1, 5.6.7.8")
    await fn(attacker_attempt_1)  # exhausts the bucket for real IP 5.6.7.8

    attacker_attempt_2 = _FakeRequest("127.0.0.1", xff="2.2.2.2, 5.6.7.8")
    # Different forged leftmost value, SAME real (rightmost) IP -- must
    # still be rate limited. Leftmost-trust would have bucketed these as
    # two distinct IPs (1.1.1.1 vs 2.2.2.2), defeating the limit entirely.
    with pytest.raises(HTTPException):
        await fn(attacker_attempt_2)

    different_real_user = _FakeRequest("127.0.0.1", xff="1.1.1.1, 9.9.9.9")
    # Same forged leftmost value as attempt_1, genuinely different
    # rightmost IP -- must NOT be rate limited (independent real user).
    await fn(different_real_user)


async def test_bucket_dict_evicts_least_recently_touched_when_over_cap(monkeypatch):
    # S-2: without a cap, one entry per distinct (ip, key) accumulates
    # forever. Bounded LRU eviction mirrors cache.py's pattern (Phase 41).
    import app.api.middleware.rate_limit as rl_module
    monkeypatch.setattr(rl_module, "_MAX_TRACKED_BUCKETS", 2)
    rl_module._windows.clear()

    fn = rate_limit("rl_evict", limit=100, window_secs=60)
    await fn(_FakeRequest("10.1.1.1"))
    await fn(_FakeRequest("10.1.1.2"))
    await fn(_FakeRequest("10.1.1.3"))  # 3rd bucket pushes total over the cap of 2

    keys = list(rl_module._windows.keys())
    assert ("10.1.1.1", "rl_evict") not in keys  # oldest-touched, evicted
    assert ("10.1.1.2", "rl_evict") in keys
    assert ("10.1.1.3", "rl_evict") in keys


async def test_touching_an_existing_bucket_protects_it_from_eviction(monkeypatch):
    import app.api.middleware.rate_limit as rl_module
    monkeypatch.setattr(rl_module, "_MAX_TRACKED_BUCKETS", 2)
    rl_module._windows.clear()

    fn = rate_limit("rl_lru", limit=100, window_secs=60)
    await fn(_FakeRequest("10.2.2.1"))
    await fn(_FakeRequest("10.2.2.2"))
    await fn(_FakeRequest("10.2.2.1"))  # re-touch -- now most-recently-used
    await fn(_FakeRequest("10.2.2.3"))  # pushes total over cap of 2

    keys = list(rl_module._windows.keys())
    # 10.2.2.2 is the least-recently-touched at this point, not 10.2.2.1.
    assert ("10.2.2.2", "rl_lru") not in keys
    assert ("10.2.2.1", "rl_lru") in keys
    assert ("10.2.2.3", "rl_lru") in keys


import pytest
from fastapi import HTTPException
from starlette.requests import Request

from app.api.middleware.rate_limit import client_ip, rate_limit


def _phase63_request(headers: dict[str, str]) -> Request:
    return Request(
        {
            "type": "http",
            "asgi": {"version": "3.0"},
            "http_version": "1.1",
            "method": "POST",
            "scheme": "https",
            "path": "/phase-63-rate-limit",
            "raw_path": b"/phase-63-rate-limit",
            "query_string": b"",
            "headers": [
                (name.lower().encode("latin-1"), value.encode("latin-1"))
                for name, value in headers.items()
            ],
            "client": ("127.0.0.1", 12345),
            "server": ("testserver", 443),
        }
    )


def test_client_ip_cf_connecting_ip_wins_over_x_forwarded_for():
    request = _phase63_request(
        {
            "CF-Connecting-IP": " 203.0.113.10 ",
            "X-Forwarded-For": "198.51.100.1, 192.0.2.1",
        }
    )

    assert client_ip(request) == "203.0.113.10"


def test_client_ip_uses_true_client_ip_before_x_forwarded_for():
    request = _phase63_request(
        {
            "True-Client-IP": " 203.0.113.11 ",
            "X-Forwarded-For": "198.51.100.2, 192.0.2.2",
        }
    )

    assert client_ip(request) == "203.0.113.11"


def test_client_ip_falls_back_to_rightmost_x_forwarded_for_entry():
    request = _phase63_request(
        {"X-Forwarded-For": "198.51.100.3, 192.0.2.3"}
    )

    assert client_ip(request) == "192.0.2.3"


def test_client_ip_ignores_empty_cf_connecting_ip():
    request = _phase63_request(
        {
            "CF-Connecting-IP": "   ",
            "True-Client-IP": " 203.0.113.12 ",
            "X-Forwarded-For": "198.51.100.4, 192.0.2.4",
        }
    )

    assert client_ip(request) == "203.0.113.12"


async def test_rate_limit_uses_cf_connecting_ip_for_a_shared_bucket():
    limiter = rate_limit("phase-63-cf-connecting-ip", 2)
    cf_connecting_ip = "198.18.63.63"

    await limiter(
        _phase63_request(
            {
                "CF-Connecting-IP": cf_connecting_ip,
                "X-Forwarded-For": "198.51.100.5, 192.0.2.5",
            }
        )
    )
    await limiter(
        _phase63_request(
            {
                "CF-Connecting-IP": cf_connecting_ip,
                "X-Forwarded-For": "198.51.100.6, 192.0.2.6",
            }
        )
    )

    with pytest.raises(HTTPException) as exc_info:
        await limiter(
            _phase63_request(
                {
                    "CF-Connecting-IP": cf_connecting_ip,
                    "X-Forwarded-For": "198.51.100.7, 192.0.2.7",
                }
            )
        )

    assert exc_info.value.status_code == 429
