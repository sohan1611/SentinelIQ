import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSON
from app.database import Base

class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), index=True)
    run_at = Column(DateTime, default=datetime.utcnow)
    integrity_score = Column(Float, nullable=True)
    financial_score = Column(Float, nullable=True)
    cashflow_score = Column(Float, nullable=True)
    governance_score = Column(Float, nullable=True)
    earnings_score = Column(Float, nullable=True)
    narrative_score = Column(Float, nullable=True)
    news_score = Column(Float, nullable=True)
    module_details = Column(JSON, nullable=True)
    status = Column(String, default="pending")
