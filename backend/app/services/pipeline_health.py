"""In-process health signals for the analysis pipeline.

This makes silent pipeline degradation observable after the yfinance outage left
financial signals unavailable for two months.  It intentionally keeps only
bounded, in-process state and performs no database I/O because Neon compute
budget must be allowed to scale to zero.  The state resets on restart, an
accepted trade also made by the reaper status and rate limiter.
"""

from collections import deque
from datetime import datetime, timezone


# `narrative` is deliberately excluded: it is zero-weighted under ADR-006.
WEIGHTED_MODULES = ("financial", "cashflow", "governance", "earnings", "news")

# Match cache.py's bounded-memory rule so a long-lived process never grows without limit.
MAX_TRACKED_ANALYSES = 50
SIGNAL_DEGRADED_THRESHOLD_PCT = 50.0
MIN_SAMPLE_FOR_DEGRADED = 3


_recent: deque = deque(maxlen=MAX_TRACKED_ANALYSES)
_last_recorded_at: datetime | None = None


def record_analysis_outcome(scores: dict, confidence: str) -> None:
    """Record one committed analysis outcome without affecting the pipeline."""
    global _last_recorded_at

    try:
        safe_scores = scores if isinstance(scores, dict) else {}
        missing_modules = []
        for module in WEIGHTED_MODULES:
            try:
                value = safe_scores.get(module)
                is_missing = module not in safe_scores or value is None
            except Exception:
                is_missing = True

            # ADR-005: absence is not neutral; a real 50.0 score is present.
            if is_missing:
                missing_modules.append(module)

        try:
            confidence_value = confidence if isinstance(confidence, str) else str(confidence)
        except Exception:
            confidence_value = ""

        _recent.append((tuple(missing_modules), confidence_value))
        _last_recorded_at = datetime.now(timezone.utc)
    except Exception:
        # Observability must never be able to interrupt the analysis pipeline.
        return


def get_pipeline_status() -> dict:
    """Return the current in-process pipeline signal health without I/O."""
    analyses_recorded = len(_recent)
    module_failures = {module: 0 for module in WEIGHTED_MODULES}
    confidence_counts = {"low": 0, "medium": 0, "high": 0}
    degraded_analyses = 0

    for missing_modules, confidence in _recent:
        if missing_modules:
            degraded_analyses += 1
        for module in missing_modules:
            module_failures[module] += 1
        confidence_counts[confidence] = confidence_counts.get(confidence, 0) + 1

    degraded_pct = (
        round((degraded_analyses / analyses_recorded) * 100, 1)
        if analyses_recorded
        else 0.0
    )

    # Avoid a false alarm from one failed analysis immediately after a restart.
    signal_degraded = (
        analyses_recorded >= MIN_SAMPLE_FOR_DEGRADED
        and degraded_pct >= SIGNAL_DEGRADED_THRESHOLD_PCT
    )

    return {
        "analyses_recorded": analyses_recorded,
        "degraded_analyses": degraded_analyses,
        "degraded_pct": degraded_pct,
        "module_failures": module_failures,
        "confidence": confidence_counts,
        "last_recorded_at": _last_recorded_at.isoformat() if _last_recorded_at else None,
        "signal_degraded": signal_degraded,
    }


def reset_pipeline_health() -> None:
    """Clear in-process state so tests do not leak outcomes between runs."""
    global _last_recorded_at

    _recent.clear()
    _last_recorded_at = None
