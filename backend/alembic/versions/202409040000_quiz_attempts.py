"""Quiz attempts and corrections.

Revision ID: 202409040000
Revises: 202409030000
Create Date: 2026-09-14 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "202409040000"
down_revision = "202409030000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "quiz_attempts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("domaine", sa.String(length=50), nullable=False),
        sa.Column("sous_theme", sa.String(length=100), nullable=True),
        sa.Column("referentiel", sa.String(length=50), nullable=True),
        sa.Column("enonce", sa.Text(), nullable=False),
        sa.Column("corrige", sa.Text(), nullable=True),
        sa.Column("reponse_etudiant", sa.Text(), nullable=True),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("feedback_corrige", sa.Text(), nullable=True),
        sa.Column("statut", sa.String(length=20), nullable=False, server_default="genere"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_quiz_attempts_id"), "quiz_attempts", ["id"], unique=False)
    op.create_index(op.f("ix_quiz_attempts_user_id"), "quiz_attempts", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_quiz_attempts_user_id"), table_name="quiz_attempts")
    op.drop_index(op.f("ix_quiz_attempts_id"), table_name="quiz_attempts")
    op.drop_table("quiz_attempts")
