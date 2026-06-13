import uuid
from sqlalchemy import Column, String, Float, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base

class NarrativeSnapshot(Base):
    __tablename__ = "narrative_snapshots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), index=True)
    period = Column(String(20))
    statement_text = Column(Text)
    sentiment_label = Column(String(20))
    sentiment_score = Column(Float)
    source = Column(String(50))
    fetched_at = Column(DateTime)
