import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base

class FinancialData(Base):
    __tablename__ = "financial_data"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), index=True)
    period = Column(String(20))
    period_type = Column(String(10))
    revenue = Column(Float, nullable=True)
    net_income = Column(Float, nullable=True)
    operating_cf = Column(Float, nullable=True)
    free_cf = Column(Float, nullable=True)
    total_debt = Column(Float, nullable=True)
    total_assets = Column(Float, nullable=True)
    accounts_recv = Column(Float, nullable=True)
    gross_margin = Column(Float, nullable=True)
    fetched_at = Column(DateTime, default=datetime.utcnow)
