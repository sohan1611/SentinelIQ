"""Structured JSON logging + correlation IDs (Phase 10 Step 4,
OPUS_ARCHITECTURAL_REVIEW.md Sec.8 item 4). JsonFormatter renders every log
record as a single-line JSON object; CorrelationLoggerAdapter merges per-call
`extra` (e.g. {"stage": "forensics"}) with the adapter's bound context
(correlation_id, ticker) so both appear together in run_full_analysis's
per-stage logs.
"""

import json
import logging

from app.logging_config import CorrelationLoggerAdapter, JsonFormatter


def _make_record(msg="hello", **extra):
    record = logging.LogRecord(
        name="app.test", level=logging.INFO, pathname=__file__, lineno=1,
        msg=msg, args=None, exc_info=None,
    )
    for key, value in extra.items():
        setattr(record, key, value)
    return record


def test_json_formatter_emits_valid_json_with_core_and_extra_fields():
    record = _make_record(correlation_id="abc-123", stage="forensics")

    payload = json.loads(JsonFormatter().format(record))

    assert payload["level"] == "INFO"
    assert payload["logger"] == "app.test"
    assert payload["message"] == "hello"
    assert payload["correlation_id"] == "abc-123"
    assert payload["stage"] == "forensics"
    assert "timestamp" in payload


def test_json_formatter_includes_exception_info():
    try:
        raise ValueError("boom")
    except ValueError:
        import sys
        record = _make_record(msg="failed")
        record.exc_info = sys.exc_info()

    payload = json.loads(JsonFormatter().format(record))

    assert "ValueError: boom" in payload["exc_info"]


def test_correlation_logger_adapter_merges_bound_and_call_extra(caplog):
    base_logger = logging.getLogger("app.test.adapter")
    adapter = CorrelationLoggerAdapter(base_logger, {"correlation_id": "abc-123", "ticker": "AAPL"})

    with caplog.at_level(logging.INFO, logger="app.test.adapter"):
        adapter.info("stage started", extra={"stage": "forensics"})

    record = caplog.records[0]
    assert record.correlation_id == "abc-123"
    assert record.ticker == "AAPL"
    assert record.stage == "forensics"


def test_correlation_logger_adapter_works_without_call_site_extra(caplog):
    base_logger = logging.getLogger("app.test.adapter2")
    adapter = CorrelationLoggerAdapter(base_logger, {"correlation_id": "abc-123", "ticker": "AAPL"})

    with caplog.at_level(logging.INFO, logger="app.test.adapter2"):
        adapter.info("analysis complete")

    record = caplog.records[0]
    assert record.correlation_id == "abc-123"
    assert record.ticker == "AAPL"


def test_secret_value_in_message_is_redacted(monkeypatch):
    from app.config import settings
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "fake-gemini-key-xyz123")
    monkeypatch.setattr(settings, "SECRET_KEY", "fake-secret-key-abc789")

    record = _make_record(msg="Gemini API error: bad request to ...?key=fake-gemini-key-xyz123")
    rendered = JsonFormatter().format(record)

    assert "fake-gemini-key-xyz123" not in rendered
    assert "***REDACTED***" in rendered


def test_secret_value_in_extra_field_is_redacted(monkeypatch):
    from app.config import settings
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "fake-gemini-key-xyz123")
    monkeypatch.setattr(settings, "SECRET_KEY", "fake-secret-key-abc789")

    record = _make_record(msg="rate_limit client_ip resolved", raw_detail="token=fake-secret-key-abc789")
    rendered = JsonFormatter().format(record)

    assert "fake-secret-key-abc789" not in rendered
    assert "***REDACTED***" in rendered


def test_ordinary_message_with_no_secret_is_unchanged(monkeypatch):
    from app.config import settings
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "fake-gemini-key-xyz123")
    monkeypatch.setattr(settings, "SECRET_KEY", "fake-secret-key-abc789")

    record = _make_record(msg="stage started", stage="forensics")
    payload = json.loads(JsonFormatter().format(record))

    assert payload["message"] == "stage started"
    assert payload["stage"] == "forensics"
    assert "REDACTED" not in json.dumps(payload)
