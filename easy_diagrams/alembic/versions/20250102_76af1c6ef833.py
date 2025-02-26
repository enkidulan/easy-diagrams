"""shortened diagram id

Revision ID: 76af1c6ef833
Revises: 26b8db5434ef
Create Date: 2025-01-02 14:34:32.764970

"""

import random
import string

import sqlalchemy as sa

from alembic import op


def _gen_diagram_id() -> str:
    """Generate a unique identifier for the diagram."""
    return "".join(random.choices(string.ascii_letters + string.digits, k=32))


# revision identifiers, used by Alembic.
revision = "76af1c6ef833"
down_revision = "26b8db5434ef"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column("diagrams", "id", new_column_name="old_id")
    op.add_column(
        "diagrams",
        sa.Column(
            "id",
            sa.String(length=32),
            nullable=True,
            primary_key=True,
            default=_gen_diagram_id,
        ),
    )
    op.execute("UPDATE diagrams SET id = LEFT(old_id, 32)")
    op.alter_column("diagrams", "id", nullable=False)
    op.drop_column("diagrams", "old_id")
    # ### end Alembic commands ###


def downgrade():
    pass
