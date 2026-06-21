"""add edgar_financial_facts table (Phase 34 -- SEC EDGAR foundation)

Revision ID: 0004
Revises: 0003
Create Date: 2026-06-21

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '0004'
down_revision: Union[str, None] = '0003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "edgar_financial_facts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("concept", sa.String(length=100), nullable=False),
        sa.Column("period_start", sa.String(length=20), nullable=True),
        sa.Column("period_end", sa.String(length=20), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("accession_number", sa.String(length=30), nullable=False),
        sa.Column("form_type", sa.String(length=20), nullable=False),
        sa.Column("filed_date", sa.String(length=20), nullable=False),
        sa.Column("fetched_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_edgar_financial_facts_company_id", "edgar_financial_facts", ["company_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_edgar_financial_facts_company_id", table_name="edgar_financial_facts")
    op.drop_table("edgar_financial_facts")
