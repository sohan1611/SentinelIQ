"""SECRET_KEY strength validation (Phase 44 Step 2 / S-1).

CLAUDE.md / .env.example document a 32-char minimum; nothing previously
enforced it. Settings() is instantiated at module import time (app/config.py),
so a violation must raise at startup, not silently produce a forgeable key.
"""
import pytest

from app.config import Settings, MIN_SECRET_KEY_LENGTH


def _settings(secret_key: str) -> Settings:
    return Settings(
        DATABASE_URL="postgresql+asyncpg://u:p@localhost/db",
        GEMINI_API_KEY="dummy",
        SECRET_KEY=secret_key,
    )


def test_secret_key_below_minimum_length_raises():
    with pytest.raises(ValueError, match="SECRET_KEY must be at least"):
        _settings("x" * (MIN_SECRET_KEY_LENGTH - 1))


def test_secret_key_at_exactly_minimum_length_is_accepted():
    settings = _settings("x" * MIN_SECRET_KEY_LENGTH)
    assert len(settings.SECRET_KEY) == MIN_SECRET_KEY_LENGTH


def test_secret_key_above_minimum_length_is_accepted():
    settings = _settings("x" * (MIN_SECRET_KEY_LENGTH + 10))
    assert len(settings.SECRET_KEY) == MIN_SECRET_KEY_LENGTH + 10


def test_empty_secret_key_raises():
    with pytest.raises(ValueError, match="SECRET_KEY must be at least"):
        _settings("")
