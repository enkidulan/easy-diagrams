"""Add organizations

Revision ID: 002_add_organizations
Revises: 001_add_folders
Create Date: 2025-01-17 12:00:00.000000

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "002_add_organizations"
down_revision = "001_add_folders"
branch_labels = None
depends_on = None


def upgrade():
    # Create organizations table
    op.create_table(
        "organizations",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True
        ),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create default organization
    op.execute(
        "INSERT INTO organizations (id, name) VALUES ('default_org', 'Default Organization')"
    )

    # Add organization_id to users table with default
    op.add_column(
        "users",
        sa.Column(
            "organization_id", sa.String(), nullable=False, server_default="default_org"
        ),
    )
    op.create_foreign_key(
        "fk_users_organization", "users", "organizations", ["organization_id"], ["id"]
    )

    # Add organization_id to diagrams table with default
    op.add_column(
        "diagrams",
        sa.Column(
            "organization_id", sa.String(), nullable=False, server_default="default_org"
        ),
    )
    op.create_foreign_key(
        "fk_diagrams_organization",
        "diagrams",
        "organizations",
        ["organization_id"],
        ["id"],
    )

    # Drop user_id column and its constraints from diagrams
    op.drop_constraint("fk_diagrams_user_id_users", "diagrams", type_="foreignkey")
    op.drop_index("ix_diagrams_user_id", table_name="diagrams")
    op.drop_column("diagrams", "user_id")

    # Add organization_id to folders table with default
    op.add_column(
        "folders",
        sa.Column(
            "organization_id", sa.String(), nullable=False, server_default="default_org"
        ),
    )
    op.create_foreign_key(
        "fk_folders_organization",
        "folders",
        "organizations",
        ["organization_id"],
        ["id"],
    )

    # Drop user_id column and its constraints from folders
    op.drop_index(op.f("ix_folders_user_id"), table_name="folders")
    op.drop_column("folders", "user_id")


def downgrade():
    # Add user_id back to folders
    op.add_column("folders", sa.Column("user_id", sa.String(), nullable=True))
    op.execute(
        "UPDATE folders SET user_id = (SELECT id FROM users WHERE users.organization_id = folders.organization_id LIMIT 1)"
    )
    op.alter_column("folders", "user_id", nullable=False)
    op.create_foreign_key(None, "folders", "users", ["user_id"], ["id"])
    op.drop_constraint("fk_folders_organization", "folders", type_="foreignkey")
    op.drop_column("folders", "organization_id")

    # Add user_id back to diagrams
    op.add_column("diagrams", sa.Column("user_id", sa.String(), nullable=True))
    op.execute(
        "UPDATE diagrams SET user_id = (SELECT id FROM users WHERE users.organization_id = diagrams.organization_id LIMIT 1)"
    )
    op.alter_column("diagrams", "user_id", nullable=False)
    op.create_foreign_key(
        "fk_diagrams_user_id_users", "diagrams", "users", ["user_id"], ["id"]
    )
    op.drop_constraint("fk_diagrams_organization", "diagrams", type_="foreignkey")
    op.drop_column("diagrams", "organization_id")

    # Remove organization_id from users
    op.drop_constraint("fk_users_organization", "users", type_="foreignkey")
    op.drop_column("users", "organization_id")

    # Drop organizations table
    op.drop_table("organizations")
