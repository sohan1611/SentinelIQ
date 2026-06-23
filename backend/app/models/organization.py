import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base

class Organization(Base):
    """E-1 scaffolding -- no multi-user org features yet (invitations,
    role enforcement, billing). Every user currently gets exactly one
    personal org whose id matches their own user id (see auth.py's
    register() and the 0008 migration's backfill) -- a deliberate
    singleton-org-per-user shape, cheap to retrofit into a real
    multi-member org later without backfilling org_id onto every
    user-scoped table from scratch.
    """
    __tablename__ = "organizations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
