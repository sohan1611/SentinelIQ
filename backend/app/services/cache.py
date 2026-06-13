from typing import Any
from datetime import datetime, timedelta

_cache: dict = {}

def get(key: str) -> Any | None:
    entry = _cache.get(key)
    if not entry:
        return None
    if datetime.utcnow() > entry["expires"]:
        del _cache[key]
        return None
    return entry["value"]

def set(key: str, value: Any, ttl_seconds: int = 3600):
    _cache[key] = {
        "value": value,
        "expires": datetime.utcnow() + timedelta(seconds=ttl_seconds)
    }
