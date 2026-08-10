from pydantic import BaseModel, EmailStr, field_validator
from uuid import UUID
from datetime import datetime
from typing import Optional

MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_BYTES = 72

class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, password: str) -> str:
        if len(password) < MIN_PASSWORD_LENGTH:
            raise ValueError(f"Password must be at least {MIN_PASSWORD_LENGTH} characters.")

        # bcrypt raises on passwords over 72 bytes; this creates a clean 422
        # instead of an unhandled 500. The limit is bytes, not characters,
        # because multi-byte UTF-8 characters can reach it sooner.
        if len(password.encode("utf-8")) > MAX_PASSWORD_BYTES:
            raise ValueError(f"Password must be at most {MAX_PASSWORD_BYTES} bytes.")

        return password

class UserResponse(UserBase):
    id: UUID
    tier: str
    created_at: datetime
    is_active: bool
    org_id: UUID
    role: str

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None
