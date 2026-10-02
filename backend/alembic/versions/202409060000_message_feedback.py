"""Add message feedback column.

Revision ID: 202409060000
Revises: 202409050000
Create Date: 2026-09-21 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "202409060000"
down_revision = "202409050000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("messages", sa.Column("feedback", sa.String(length=10), nullable=True))


def downgrade() -> None:
    op.drop_column("messages", "feedback")
