import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base

class EdgarFinancialFact(Base):
    """One reported value for one XBRL concept, for one period, from one
    filing. A company can have multiple rows for the same concept+period
    when a later filing (e.g. a 10-K/A) restates an earlier one -- that
    multiplicity is the point; this table is deliberately NOT shaped like
    FinancialData's one-value-per-period model. See Phase 34/35 in
    MASTER_IMPLEMENTATION_PLAN.md."""
    __tablename__ = "edgar_financial_facts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), index=True)
    concept = Column(String(100), nullable=False)
    period_start = Column(String(20), nullable=True)
    period_end = Column(String(20), nullable=False)
    value = Column(Float, nullable=False)
    accession_number = Column(String(30), nullable=False)
    form_type = Column(String(20), nullable=False)
    filed_date = Column(String(20), nullable=False)
    fetched_at = Column(DateTime, default=datetime.utcnow)
