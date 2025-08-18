"""add organization owners table

Revision ID: add_org_owners_simple
Revises: 5d3dee30022c
Create Date: 2025-01-03 00:00:00.000000

"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "add_org_owners_simple"
down_revision = "002_add_organizations"
branch_labels = None
depends_on = None


def upgrade():
    # Create organization_owners table (assuming organizations table exists)
    op.create_table(
        "organization_owners",
        sa.Column("organization_id", sa.String(), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("organization_id", "user_id"),
    )


def downgrade():
    op.drop_table("organization_owners")
