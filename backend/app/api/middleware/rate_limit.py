"""In-memory sliding-window rate limiter (ADR-008 — single-instance only).

Resets on process restart; does not coordinate across multiple instances.
Use as a FastAPI dependency via the rate_limit() factory:

    @router.post("/login", dependencies=[Depends(rate_limit("login", 10))])
"""
import logging
from collections import OrderedDict
from datetime import datetime, timezone
from typing import Callable

from fastapi import HTTPException, Request

logger = logging.getLogger(__name__)

_WINDOW_SECS = 60
# S-2: without a cap, one entry per distinct (ip, key) pair accumulates
# forever -- pruned only on the NEXT hit to that exact bucket, so one-off or
# scanning traffic (each from a distinct real IP) leaks memory indefinitely.
# Bounded LRU eviction mirrors cache.py's established pattern (Phase 41).
# Gameable only by manufacturing many fake bucket keys cheaply -- closed by
# H-2's fix above (client_ip() no longer trusts attacker-supplied values).
_MAX_TRACKED_BUCKETS = 10_000
_windows: "OrderedDict[tuple[str, str], list[float]]" = OrderedDict()


def client_ip(request: Request) -> str:
    """Returns the bucket key used for rate limiting -- must not be an
    attacker-controlled value (H-2).

    X-Forwarded-For's leftmost entry is whatever the original client
    claimed -- on Render (Client -> Cloudflare -> Render's load balancer ->
    this app), only entries appended by our OWN trusted infrastructure are
    reliable, and each proxy hop appends to the RIGHT. An attacker can put
    any fake value(s) at the left; they cannot control what's appended
    after their request leaves their own machine. Taking the rightmost
    entry is the standard fix for this class of bug regardless of the
    exact trusted-hop count.

    Logged at INFO (not just debug) so the raw header is visible in
    Render's live log stream -- the exact hop shape Render forwards isn't
    fully verifiable without live traffic (confirmed inconsistent/disputed
    even in Render's own community), so this is the follow-up empirical
    check: the rightmost entry must vary across distinct real users, not
    sit constant (which would silently make rate limiting useless in the
    opposite direction by bucketing everyone together).
    """
    xff = request.headers.get("x-forwarded-for")
    if xff:
        entries = [e.strip() for e in xff.split(",") if e.strip()]
        ip = entries[-1] if entries else (request.client.host if request.client else "unknown")
        logger.info("rate_limit client_ip resolved", extra={"xff_raw": xff, "resolved_ip": ip})
        return ip
    return request.client.host if request.client else "unknown"


def rate_limit(key: str, limit: int, window_secs: int = _WINDOW_SECS) -> Callable:
    """Return a FastAPI dependency that enforces per-IP sliding-window rate limiting.

    Args:
        key: Logical bucket name, e.g. "login", "register", "analysis_run".
        limit: Max requests allowed within window_secs from a single IP.
        window_secs: Rolling window duration in seconds (default 60).
    """
    async def _check(request: Request) -> None:
        ip = client_ip(request)
        bucket = (ip, key)
        now = datetime.now(timezone.utc).timestamp()
        cutoff = now - window_secs

        pruned = [t for t in _windows.get(bucket, []) if t > cutoff]

        if len(pruned) >= limit:
            _windows[bucket] = pruned
            _windows.move_to_end(bucket)
            retry_after = max(1, int(pruned[0] + window_secs - now) + 1)
            raise HTTPException(
                status_code=429,
                detail={
                    "error": {
                        "code": "RATE_LIMITED",
                        "message": f"Too many requests. Limit is {limit} per {window_secs}s.",
                    }
                },
                headers={"Retry-After": str(retry_after)},
            )

        pruned.append(now)
        _windows[bucket] = pruned
        _windows.move_to_end(bucket)
        while len(_windows) > _MAX_TRACKED_BUCKETS:
            _windows.popitem(last=False)

    return _check
