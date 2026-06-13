import uuid
from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base

class RedFlag(Base):
    __tablename__ = "red_flags"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    analysis_id = Column(UUID(as_uuid=True), ForeignKey("analysis_results.id"))
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), index=True)
    flag_type = Column(String(50))
    severity = Column(String(20))
    description = Column(Text)
    period = Column(String(20), nullable=True)
    event_date = Column(DateTime, nullable=True)
