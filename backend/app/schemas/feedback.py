from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class FeedbackRequest(BaseModel):
    analysis_id: UUID
    flag_id: Optional[UUID] = None
    message: str = Field(..., min_length=1, max_length=1000)


class FeedbackResponse(BaseModel):
    message: str
