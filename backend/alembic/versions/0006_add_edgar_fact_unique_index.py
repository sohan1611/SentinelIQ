"""add unique index on edgar_financial_facts to stop unbounded duplication (Phase 41 / H-4)

Revision ID: 0006
Revises: 0005
Create Date: 2026-06-22

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '0006'
down_revision: Union[str, None] = '0005'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Expression-based (not a plain column-list UniqueConstraint) because
    # period_start is nullable -- standard SQL treats every NULL as distinct
    # from every other NULL, so a plain unique constraint would silently fail
    # to deduplicate point-in-time concepts (e.g. total_assets) that have no
    # period_start at all. accession_number stays part of the key
    # deliberately -- multiple genuinely different filings for the same
    # period must still coexist; this only blocks re-inserting the identical
    # filing on a later analysis run.
    op.execute("""
        CREATE UNIQUE INDEX ix_edgar_financial_facts_unique_fact
        ON edgar_financial_facts (company_id, concept, COALESCE(period_start, ''), period_end, accession_number)
    """)


def downgrade() -> None:
    op.execute("DROP INDEX ix_edgar_financial_facts_unique_fact")
