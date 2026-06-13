import uuid
from datetime import datetime
from sqlalchemy import Column, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base

class Report(Base):
    __tablename__ = "reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), index=True)
    analysis_id = Column(UUID(as_uuid=True), ForeignKey("analysis_results.id"))
    content = Column(Text)
    generated_at = Column(DateTime, default=datetime.utcnow)
