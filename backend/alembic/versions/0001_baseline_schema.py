"""baseline schema - 8 core tables

Revision ID: 0001
Revises:
Create Date: 2026-06-15

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '0001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("hashed_pw", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=True),
        sa.Column("tier", sa.String(length=20), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "companies",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("ticker", sa.String(length=20), nullable=False),
        sa.Column("sector", sa.String(length=100), nullable=True),
        sa.Column("exchange", sa.String(length=50), nullable=True),
        sa.Column("last_analyzed", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_companies_ticker", "companies", ["ticker"], unique=True)

    op.create_table(
        "financial_data",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("period", sa.String(length=20), nullable=True),
        sa.Column("period_type", sa.String(length=10), nullable=True),
        sa.Column("revenue", sa.Float(), nullable=True),
        sa.Column("net_income", sa.Float(), nullable=True),
        sa.Column("operating_cf", sa.Float(), nullable=True),
        sa.Column("free_cf", sa.Float(), nullable=True),
        sa.Column("total_debt", sa.Float(), nullable=True),
        sa.Column("total_assets", sa.Float(), nullable=True),
        sa.Column("accounts_recv", sa.Float(), nullable=True),
        sa.Column("gross_margin", sa.Float(), nullable=True),
        sa.Column("fetched_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_financial_data_company_id", "financial_data", ["company_id"])

    op.create_table(
        "analysis_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("run_at", sa.DateTime(), nullable=True),
        sa.Column("integrity_score", sa.Float(), nullable=True),
        sa.Column("financial_score", sa.Float(), nullable=True),
        sa.Column("cashflow_score", sa.Float(), nullable=True),
        sa.Column("governance_score", sa.Float(), nullable=True),
        sa.Column("earnings_score", sa.Float(), nullable=True),
        sa.Column("narrative_score", sa.Float(), nullable=True),
        sa.Column("news_score", sa.Float(), nullable=True),
        sa.Column("module_details", postgresql.JSON(), nullable=True),
        sa.Column("status", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_analysis_results_company_id", "analysis_results", ["company_id"])

    op.create_table(
        "red_flags",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("analysis_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("flag_type", sa.String(length=50), nullable=True),
        sa.Column("severity", sa.String(length=20), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("period", sa.String(length=20), nullable=True),
        sa.Column("event_date", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["analysis_id"], ["analysis_results.id"]),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_red_flags_company_id", "red_flags", ["company_id"])

    op.create_table(
        "reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("analysis_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("generated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["analysis_id"], ["analysis_results.id"]),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_reports_company_id", "reports", ["company_id"])

    op.create_table(
        "watchlist",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("added_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "company_id", name="_user_company_uc"),
    )
    op.create_index("ix_watchlist_user_id", "watchlist", ["user_id"])

    op.create_table(
        "narrative_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("period", sa.String(length=20), nullable=True),
        sa.Column("statement_text", sa.Text(), nullable=True),
        sa.Column("sentiment_label", sa.String(length=20), nullable=True),
        sa.Column("sentiment_score", sa.Float(), nullable=True),
        sa.Column("source", sa.String(length=50), nullable=True),
        sa.Column("fetched_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_narrative_snapshots_company_id", "narrative_snapshots", ["company_id"])


def downgrade() -> None:
    op.drop_index("ix_narrative_snapshots_company_id", table_name="narrative_snapshots")
    op.drop_table("narrative_snapshots")

    op.drop_index("ix_watchlist_user_id", table_name="watchlist")
    op.drop_table("watchlist")

    op.drop_index("ix_reports_company_id", table_name="reports")
    op.drop_table("reports")

    op.drop_index("ix_red_flags_company_id", table_name="red_flags")
    op.drop_table("red_flags")

    op.drop_index("ix_analysis_results_company_id", table_name="analysis_results")
    op.drop_table("analysis_results")

    op.drop_index("ix_financial_data_company_id", table_name="financial_data")
    op.drop_table("financial_data")

    op.drop_index("ix_companies_ticker", table_name="companies")
    op.drop_table("companies")

    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
