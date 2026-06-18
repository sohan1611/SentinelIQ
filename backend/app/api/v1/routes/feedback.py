import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.api.middleware.rate_limit import _windows
from app.models.user import User
from app.schemas.feedback import FeedbackRequest, FeedbackResponse

router = APIRouter()
logger = logging.getLogger(__name__)

_FEEDBACK_DAILY_LIMIT = 5
_FEEDBACK_WINDOW_SECS = 86400  # 24 hours per user


@router.post("/analysis-error", response_model=FeedbackResponse)
async def report_analysis_error(
    request: FeedbackRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Per-user daily rate limit reusing the same sliding-window store (ADR-008)
    bucket = (str(current_user.id), "feedback")
    now = datetime.now(timezone.utc).timestamp()
    cutoff = now - _FEEDBACK_WINDOW_SECS
    pruned = [t for t in _windows[bucket] if t > cutoff]
    _windows[bucket] = pruned
    if len(pruned) >= _FEEDBACK_DAILY_LIMIT:
        raise HTTPException(
            status_code=429,
            detail={
                "error": {
                    "code": "RATE_LIMITED",
                    "message": "Feedback limit reached. Max 5 reports per day.",
                }
            },
            headers={"Retry-After": "86400"},
        )
    _windows[bucket].append(now)

    # Persist to Render's structured log stream — no new DB table needed at this stage.
    # The JSON formatter in logging_config.py ensures these fields appear in every log line.
    logger.warning(
        "analysis_error_report",
        extra={
            "analysis_id": str(request.analysis_id),
            "flag_id": str(request.flag_id) if request.flag_id else None,
            "user_id": str(current_user.id),
            "feedback_message": request.message,
        },
    )

    return FeedbackResponse(message="Feedback received")
