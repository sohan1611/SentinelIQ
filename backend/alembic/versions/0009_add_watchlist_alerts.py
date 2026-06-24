"""add watchlist_alerts table (Phase 47 / E-4)

Revision ID: 0009
Revises: 0008
Create Date: 2026-06-24

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '0009'
down_revision: Union[str, None] = '0008'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "watchlist_alerts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("analysis_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("previous_score", sa.Float(), nullable=False),
        sa.Column("new_score", sa.Float(), nullable=False),
        sa.Column("previous_risk", sa.String(length=20), nullable=False),
        sa.Column("new_risk", sa.String(length=20), nullable=False),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"]),
        sa.ForeignKeyConstraint(["analysis_id"], ["analysis_results.id"]),
    )
    op.create_index(
        "ix_watchlist_alerts_user_created_at", "watchlist_alerts", ["user_id", "created_at"]
    )
    op.create_index(
        op.f("ix_watchlist_alerts_user_id"), "watchlist_alerts", ["user_id"]
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_watchlist_alerts_user_id"), table_name="watchlist_alerts")
    op.drop_index("ix_watchlist_alerts_user_created_at", table_name="watchlist_alerts")
    op.drop_table("watchlist_alerts")
