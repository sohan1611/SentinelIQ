import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Index, JSON
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base

class AuditLog(Base):
    """Phase 38 (F6, scoped to audit logging -- see MASTER_IMPLEMENTATION_
    PLAN.md): append-only. No update/delete endpoint exists for this table,
    ever -- that's the entire point of an audit log."""
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    action = Column(String(50), nullable=False)
    detail = Column(JSON, nullable=True)
    ip_address = Column(String(45), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_audit_logs_user_created_at", "user_id", "created_at"),
    )
