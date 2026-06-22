from collections import OrderedDict
from typing import Any
from datetime import datetime, timedelta, timezone

# Generous-but-finite bound (Phase 41 / A-3): without a cap, every distinct
# ticker ever analyzed leaves cached company/financials/news/EDGAR entries
# resident for the life of the process, growing without bound. 500 entries
# comfortably covers this project's realistic scale (a handful of keys per
# analyzed ticker) while guaranteeing memory can never grow past a fixed
# ceiling. Tune if real usage proves it too small/large.
MAX_CACHE_ENTRIES = 500

_cache: OrderedDict = OrderedDict()

def get(key: str) -> Any | None:
    entry = _cache.get(key)
    if not entry:
        return None
    if datetime.now(timezone.utc) > entry["expires"]:
        del _cache[key]
        return None
    _cache.move_to_end(key)
    return entry["value"]

def set(key: str, value: Any, ttl_seconds: int = 3600):
    _cache[key] = {
        "value": value,
        "expires": datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)
    }
    _cache.move_to_end(key)
    while len(_cache) > MAX_CACHE_ENTRIES:
        _cache.popitem(last=False)
