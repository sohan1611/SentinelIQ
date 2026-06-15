import uuid
from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base

class AnalysisRun(Base):
    __tablename__ = "analysis_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), index=True)
    analysis_result_id = Column(UUID(as_uuid=True), ForeignKey("analysis_results.id"))
    run_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_analysis_runs_user_run_at", "user_id", "run_at"),
    )
