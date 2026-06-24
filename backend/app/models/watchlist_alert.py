import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base

class WatchlistAlert(Base):
    """Phase 47 / E-4: a risk-band change on a watched company, one row per
    watching user. Distinct from RedFlag (a forensic finding tied to one
    analysis) and AuditLog (an immutable internal audit trail) -- this is a
    cross-analysis, per-user, mutable-read-state notification."""
    __tablename__ = "watchlist_alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"))
    analysis_id = Column(UUID(as_uuid=True), ForeignKey("analysis_results.id"))
    previous_score = Column(Float, nullable=False)
    new_score = Column(Float, nullable=False)
    previous_risk = Column(String(20), nullable=False)
    new_risk = Column(String(20), nullable=False)
    is_read = Column(Boolean, nullable=False, default=False, server_default="false")
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_watchlist_alerts_user_created_at", "user_id", "created_at"),
    )
