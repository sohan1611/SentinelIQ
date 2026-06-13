import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base

class Company(Base):
    __tablename__ = "companies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    ticker = Column(String(20), unique=True, index=True, nullable=False)
    sector = Column(String(100))
    exchange = Column(String(50))
    last_analyzed = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
