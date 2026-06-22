"""Unit tests for the in-memory cache (Phase 41 / A-3): bounded size with
LRU eviction, on top of the existing lazy TTL expiry. No test file existed
for this module before this phase.
"""
from datetime import datetime, timedelta, timezone

from app.services import cache


def setup_function():
    """Each test starts from a clean slate -- the cache is a process-level
    module global shared across the whole test session."""
    cache._cache.clear()


def test_set_then_get_returns_the_value():
    cache.set("k1", "v1")
    assert cache.get("k1") == "v1"


def test_get_missing_key_returns_none():
    assert cache.get("does-not-exist") is None


def test_expired_entry_returns_none_and_is_removed():
    cache.set("k1", "v1", ttl_seconds=-1)  # already expired
    assert cache.get("k1") is None
    assert "k1" not in cache._cache


def test_cache_never_exceeds_max_entries():
    for i in range(cache.MAX_CACHE_ENTRIES + 50):
        cache.set(f"key-{i}", i)
    assert len(cache._cache) == cache.MAX_CACHE_ENTRIES


def test_eviction_removes_least_recently_used_not_most_recent():
    for i in range(cache.MAX_CACHE_ENTRIES):
        cache.set(f"key-{i}", i)

    # Touch the oldest key so it becomes most-recently-used right before the
    # cache overflows -- it must survive eviction; an untouched middle key
    # must not.
    cache.get("key-0")
    cache.set(f"key-{cache.MAX_CACHE_ENTRIES}", "overflow")

    assert cache.get("key-0") == 0
    assert cache.get("key-1") is None


def test_existing_consumers_unaffected_by_signature():
    """Every caller (sec_edgar.py, news_aggregator.py, yahoo_finance.py) uses
    get(key) / set(key, value, ttl_seconds=...) -- confirm both still accept
    exactly that calling convention."""
    cache.set("ttl-key", {"nested": "value"}, ttl_seconds=7200)
    assert cache.get("ttl-key") == {"nested": "value"}
