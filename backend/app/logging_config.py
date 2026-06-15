import json
import logging

_RESERVED_LOG_RECORD_ATTRS = frozenset({
    "args", "asctime", "created", "exc_info", "exc_text", "filename",
    "funcName", "levelname", "levelno", "lineno", "message", "module",
    "msecs", "msg", "name", "pathname", "process", "processName",
    "relativeCreated", "stack_info", "thread", "threadName", "taskName",
})


class JsonFormatter(logging.Formatter):
    """Renders each LogRecord as a single-line JSON object.

    Fields passed via logging's `extra=` kwarg (e.g. correlation_id, ticker,
    stage -- see CorrelationLoggerAdapter) are included alongside the
    standard timestamp/level/logger/message fields.
    """

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        for key, value in record.__dict__.items():
            if key not in _RESERVED_LOG_RECORD_ATTRS:
                payload[key] = value

        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)

        return json.dumps(payload, default=str)


class CorrelationLoggerAdapter(logging.LoggerAdapter):
    """LoggerAdapter that merges per-call `extra` with the bound context.

    The stdlib LoggerAdapter.process() overwrites kwargs["extra"] with
    self.extra, discarding any extra passed at the call site. This merges
    both, so e.g. log.error(msg, extra={"stage": "forensics"}) keeps the
    adapter's bound correlation_id/ticker alongside the call's stage.
    """

    def process(self, msg, kwargs):
        kwargs["extra"] = {**self.extra, **kwargs.get("extra", {})}
        return msg, kwargs


def configure_logging(level: int = logging.INFO) -> None:
    """Configure the root logger to emit single-line JSON records.

    Called once at process startup (main.py) -- every module's
    `logging.getLogger(__name__)` logger propagates to the root logger and
    inherits this formatter.
    """
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())

    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level)
