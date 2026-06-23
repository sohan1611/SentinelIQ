"""add organizations table + users.org_id/role, backfill one personal org per existing user (Phase 46 / E-1)

Revision ID: 0008
Revises: 0007
Create Date: 2026-06-23

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '0008'
down_revision: Union[str, None] = '0007'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "organizations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    # Nullable first -- existing rows can't satisfy NOT NULL until backfilled.
    op.add_column("users", sa.Column("org_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column(
        "users",
        sa.Column("role", sa.String(length=20), nullable=False, server_default="owner"),
    )
    op.create_foreign_key("fk_users_org_id_organizations", "users", "organizations", ["org_id"], ["id"])

    # Backfill: one personal org per existing user, reusing the user's own
    # id as their org's id -- a clean 1:1 correlation with no temporary
    # mapping table needed (organizations.id and users.id are independent
    # primary key spaces, so no collision risk).
    op.execute("""
        INSERT INTO organizations (id, name, created_at)
        SELECT id, COALESCE(full_name, email) || '''s Organization', created_at
        FROM users
    """)
    op.execute("UPDATE users SET org_id = id WHERE org_id IS NULL")

    op.alter_column("users", "org_id", nullable=False)


def downgrade() -> None:
    op.drop_constraint("fk_users_org_id_organizations", "users", type_="foreignkey")
    op.drop_column("users", "role")
    op.drop_column("users", "org_id")
    op.drop_table("organizations")
