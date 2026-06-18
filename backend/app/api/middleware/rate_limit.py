"""In-memory sliding-window rate limiter (ADR-008 — single-instance only).

Resets on process restart; does not coordinate across multiple instances.
Use as a FastAPI dependency via the rate_limit() factory:

    @router.post("/login", dependencies=[Depends(rate_limit("login", 10))])
"""
from collections import defaultdict
from datetime import datetime, timezone
from typing import Callable

from fastapi import HTTPException, Request

_WINDOW_SECS = 60
_windows: dict[tuple[str, str], list[float]] = defaultdict(list)


def _client_ip(request: Request) -> str:
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def rate_limit(key: str, limit: int, window_secs: int = _WINDOW_SECS) -> Callable:
    """Return a FastAPI dependency that enforces per-IP sliding-window rate limiting.

    Args:
        key: Logical bucket name, e.g. "login", "register", "analysis_run".
        limit: Max requests allowed within window_secs from a single IP.
        window_secs: Rolling window duration in seconds (default 60).
    """
    async def _check(request: Request) -> None:
        ip = _client_ip(request)
        bucket = (ip, key)
        now = datetime.now(timezone.utc).timestamp()
        cutoff = now - window_secs

        pruned = [t for t in _windows[bucket] if t > cutoff]
        _windows[bucket] = pruned

        if len(pruned) >= limit:
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

        _windows[bucket].append(now)

    return _check
