"""Rework organization users to use secondary table

Revision ID: 003_rework_organization_users
Revises: merge_heads
Create Date: 2025-01-17 15:00:00.000000

"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "003_rework_organization_users"
down_revision = "merge_heads"
branch_labels = None
depends_on = None


def upgrade():
    # Create new organization_users table
    op.create_table(
        "organization_users",
        sa.Column("organization_id", sa.String(), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("is_owner", sa.Boolean(), nullable=False, server_default="false"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("organization_id", "user_id"),
    )

    # Migrate existing users to organization_users table
    op.execute(
        """
        INSERT INTO organization_users (organization_id, user_id, is_owner)
        SELECT organization_id, id, false
        FROM users
        WHERE organization_id IS NOT NULL
    """
    )

    # Migrate existing owners from organization_owners to organization_users
    op.execute(
        """
        UPDATE organization_users 
        SET is_owner = true 
        WHERE (organization_id, user_id) IN (
            SELECT organization_id, user_id FROM organization_owners
        )
    """
    )

    # Drop old tables and columns
    op.drop_table("organization_owners")
    op.drop_column("users", "organization_id")


def downgrade():
    # Add organization_id back to users
    op.add_column("users", sa.Column("organization_id", sa.String(), nullable=True))

    # Recreate organization_owners table
    op.create_table(
        "organization_owners",
        sa.Column("organization_id", sa.String(), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("organization_id", "user_id"),
    )

    # Migrate data back
    op.execute(
        """
        UPDATE users 
        SET organization_id = ou.organization_id
        FROM organization_users ou
        WHERE users.id = ou.user_id
    """
    )

    op.execute(
        """
        INSERT INTO organization_owners (organization_id, user_id)
        SELECT organization_id, user_id
        FROM organization_users
        WHERE is_owner = true
    """
    )

    # Make organization_id not nullable
    op.alter_column("users", "organization_id", nullable=False)

    # Drop new table
    op.drop_table("organization_users")
