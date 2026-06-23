from sqlalchemy import Column, Date, Integer
from app.database import Base

class GeminiDailyBudget(Base):
    """Persisted Gemini call counter, keyed by UTC date (A-4).

    One row per UTC day -- the date itself is the rollover mechanism, no
    separate reset logic needed. Replaces the old in-process dict, which
    reset on every Render restart and defeated the daily cap it existed
    to enforce.
    """
    __tablename__ = "gemini_daily_budget"

    date = Column(Date, primary_key=True)
    count = Column(Integer, nullable=False, default=0)
