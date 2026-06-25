from datetime import datetime
from sqlalchemy import Column, String, DateTime
from app.database import Base

class RevokedToken(Base):
    """Phase 53 (E-2 free scaffolding): a JWT's jti, revoked before its
    natural expiry (e.g. on logout). expires_at mirrors the token's own exp
    claim -- once that passes, jose.jwt.decode already rejects the token
    regardless of this table, so a row only needs to outlive the token's
    natural lifetime. Rows past expires_at are pruned opportunistically
    whenever a new token is revoked, keeping this table bounded without a
    dedicated background loop."""
    __tablename__ = "revoked_tokens"

    jti = Column(String(36), primary_key=True)
    expires_at = Column(DateTime, nullable=False)
    revoked_at = Column(DateTime, default=datetime.utcnow)
