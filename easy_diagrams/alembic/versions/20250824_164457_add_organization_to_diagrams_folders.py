"""add organization_id to diagrams and folders

Revision ID: 164457
Revises: f4314f251172
Create Date: 2025-08-24 16:44:57.000000

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "164457"
down_revision = "f4314f251172"
branch_labels = None
depends_on = None


def upgrade():
    # Add organization_id column to diagrams table
    op.add_column("diagrams", sa.Column("organization_id", sa.UUID(), nullable=True))
    op.create_foreign_key(
        op.f("fk_diagrams_organization_id_organizations"),
        "diagrams",
        "organizations",
        ["organization_id"],
        ["id"],
    )
    op.create_index(
        op.f("ix_diagrams_organization_id"), "diagrams", ["organization_id"]
    )

    # Add organization_id column to folders table
    op.add_column("folders", sa.Column("organization_id", sa.UUID(), nullable=True))
    op.create_foreign_key(
        op.f("fk_folders_organization_id_organizations"),
        "folders",
        "organizations",
        ["organization_id"],
        ["id"],
    )
    op.create_index(op.f("ix_folders_organization_id"), "folders", ["organization_id"])

    # Data migration: Set organization_id for existing diagrams and folders
    from sqlalchemy.sql import text

    connection = op.get_bind()

    # Update diagrams with user's organization
    connection.execute(
        text(
            """
            UPDATE diagrams 
            SET organization_id = (
                SELECT ou.organization_id 
                FROM organization_users ou 
                WHERE ou.user_id = diagrams.user_id 
                LIMIT 1
            )
        """
        )
    )

    # Update folders with user's organization
    connection.execute(
        text(
            """
            UPDATE folders 
            SET organization_id = (
                SELECT ou.organization_id 
                FROM organization_users ou 
                WHERE ou.user_id = folders.user_id 
                LIMIT 1
            )
        """
        )
    )

    # Make organization_id NOT NULL after data migration
    op.alter_column("diagrams", "organization_id", nullable=False)
    op.alter_column("folders", "organization_id", nullable=False)


def downgrade():
    # Remove indexes and foreign keys
    op.drop_index(op.f("ix_folders_organization_id"), table_name="folders")
    op.drop_constraint(
        op.f("fk_folders_organization_id_organizations"),
        "folders",
        type_="foreignkey",
    )
    op.drop_column("folders", "organization_id")

    op.drop_index(op.f("ix_diagrams_organization_id"), table_name="diagrams")
    op.drop_constraint(
        op.f("fk_diagrams_organization_id_organizations"),
        "diagrams",
        type_="foreignkey",
    )
    op.drop_column("diagrams", "organization_id")
