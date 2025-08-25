"""remove user_id from diagrams and folders

Revision ID: 164500
Revises: 164457
Create Date: 2025-08-24 16:45:00.000000

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "164500"
down_revision = "164457"
branch_labels = None
depends_on = None


def upgrade():
    # Remove user_id foreign key and column from diagrams table
    op.drop_constraint("fk_diagrams_user_id_users", "diagrams", type_="foreignkey")
    op.drop_index("ix_diagrams_user_id", table_name="diagrams")
    op.drop_column("diagrams", "user_id")

    # Remove user_id foreign key and column from folders table
    op.drop_constraint("fk_folders_user_id_users", "folders", type_="foreignkey")
    op.drop_index("ix_folders_user_id", table_name="folders")
    op.drop_column("folders", "user_id")


def downgrade():
    # Add user_id column back to diagrams table
    op.add_column("diagrams", sa.Column("user_id", sa.UUID(), nullable=True))
    op.create_index("ix_diagrams_user_id", "diagrams", ["user_id"])
    op.create_foreign_key(
        "fk_diagrams_user_id_users",
        "diagrams",
        "users",
        ["user_id"],
        ["id"],
    )

    # Add user_id column back to folders table
    op.add_column("folders", sa.Column("user_id", sa.UUID(), nullable=True))
    op.create_index("ix_folders_user_id", "folders", ["user_id"])
    op.create_foreign_key(
        "fk_folders_user_id_users",
        "folders",
        "users",
        ["user_id"],
        ["id"],
    )
