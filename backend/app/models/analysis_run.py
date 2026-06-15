import uuid
from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, text
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base

class AnalysisRun(Base):
    __tablename__ = "analysis_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), index=True)
    analysis_result_id = Column(UUID(as_uuid=True), ForeignKey("analysis_results.id"))
    run_at = Column(DateTime, default=datetime.utcnow)
    # ADR-013 (Ruling A): true for a fresh computation, false for a cache-hit
    # re-open. Only counted=true rows consume the free-tier monthly quota.
    counted = Column(Boolean, nullable=False, default=True, server_default=text("true"))

    __table_args__ = (
        Index("ix_analysis_runs_user_run_at", "user_id", "run_at"),
    )
