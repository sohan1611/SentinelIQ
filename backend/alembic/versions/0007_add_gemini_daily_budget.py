"""add gemini_daily_budget table to persist the daily call counter across restarts (Phase 45 / A-4)

Revision ID: 0007
Revises: 0006
Create Date: 2026-06-23

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0007'
down_revision: Union[str, None] = '0006'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "gemini_daily_budget",
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("count", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("date"),
    )


def downgrade() -> None:
    op.drop_table("gemini_daily_budget")
