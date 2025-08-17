"""Add folders table and folder_id to diagrams

Revision ID: 001_add_folders
Revises: 5d3dee30022c
Create Date: 2024-01-01 00:00:00.000000

"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "001_add_folders"
down_revision = "5d3dee30022c"
branch_labels = None
depends_on = None


def upgrade():
    # Create folders table
    op.create_table(
        "folders",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("parent_id", sa.String(length=32), nullable=True),
        sa.ForeignKeyConstraint(
            ["parent_id"],
            ["folders.id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_folders_created_at"), "folders", ["created_at"], unique=False
    )
    op.create_index(op.f("ix_folders_name"), "folders", ["name"], unique=False)
    op.create_index(
        op.f("ix_folders_parent_id"), "folders", ["parent_id"], unique=False
    )
    op.create_index(
        op.f("ix_folders_updated_at"), "folders", ["updated_at"], unique=False
    )
    op.create_index(op.f("ix_folders_user_id"), "folders", ["user_id"], unique=False)

    # Add folder_id column to diagrams table
    op.add_column(
        "diagrams", sa.Column("folder_id", sa.String(length=32), nullable=True)
    )
    op.create_index(
        op.f("ix_diagrams_folder_id"), "diagrams", ["folder_id"], unique=False
    )
    op.create_foreign_key(None, "diagrams", "folders", ["folder_id"], ["id"])


def downgrade():
    # Remove folder_id from diagrams table
    op.drop_constraint(None, "diagrams", type_="foreignkey")
    op.drop_index(op.f("ix_diagrams_folder_id"), table_name="diagrams")
    op.drop_column("diagrams", "folder_id")

    # Drop folders table
    op.drop_index(op.f("ix_folders_user_id"), table_name="folders")
    op.drop_index(op.f("ix_folders_updated_at"), table_name="folders")
    op.drop_index(op.f("ix_folders_parent_id"), table_name="folders")
    op.drop_index(op.f("ix_folders_name"), table_name="folders")
    op.drop_index(op.f("ix_folders_created_at"), table_name="folders")
    op.drop_table("folders")
