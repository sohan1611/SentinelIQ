"""add analysis_runs table

Revision ID: 0002
Revises: 0001
Create Date: 2026-06-15

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '0002'
down_revision: Union[str, None] = '0001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "analysis_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("analysis_result_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("run_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["analysis_result_id"], ["analysis_results.id"]),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_analysis_runs_user_id", "analysis_runs", ["user_id"])
    op.create_index("ix_analysis_runs_company_id", "analysis_runs", ["company_id"])
    op.create_index("ix_analysis_runs_user_run_at", "analysis_runs", ["user_id", "run_at"])


def downgrade() -> None:
    op.drop_index("ix_analysis_runs_user_run_at", table_name="analysis_runs")
    op.drop_index("ix_analysis_runs_company_id", table_name="analysis_runs")
    op.drop_index("ix_analysis_runs_user_id", table_name="analysis_runs")
    op.drop_table("analysis_runs")
