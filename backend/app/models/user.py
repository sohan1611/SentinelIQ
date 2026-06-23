import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_pw = Column(String(255), nullable=False)
    full_name = Column(String(255))
    tier = Column(String(20), default="free")
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    # E-1 scaffolding: every user has exactly one personal org today (no
    # multi-member orgs, no role enforcement yet -- see organization.py).
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    role = Column(String(20), nullable=False, default="owner", server_default="owner")
