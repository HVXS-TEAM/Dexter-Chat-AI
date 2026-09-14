"""Create classes and memberships.

Revision ID: 202409050000
Revises: 202409040000
Create Date: 2026-09-13 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "202409050000"
down_revision = "202409040000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "classes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("professeur_id", sa.Integer(), nullable=False),
        sa.Column("nom", sa.String(length=255), nullable=False),
        sa.Column("code_invitation", sa.String(length=12), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["professeur_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_classes_id"), "classes", ["id"], unique=False)
    op.create_index(op.f("ix_classes_professeur_id"), "classes", ["professeur_id"], unique=False)
    op.create_index(op.f("ix_classes_code_invitation"), "classes", ["code_invitation"], unique=True)

    op.create_table(
        "classe_membres",
        sa.Column("classe_id", sa.Integer(), nullable=False),
        sa.Column("etudiant_id", sa.Integer(), nullable=False),
        sa.Column("joined_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["classe_id"], ["classes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["etudiant_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("classe_id", "etudiant_id"),
    )
    op.create_index(op.f("ix_classe_membres_classe_id"), "classe_membres", ["classe_id"], unique=False)
    op.create_index(op.f("ix_classe_membres_etudiant_id"), "classe_membres", ["etudiant_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_classe_membres_etudiant_id"), table_name="classe_membres")
    op.drop_index(op.f("ix_classe_membres_classe_id"), table_name="classe_membres")
    op.drop_table("classe_membres")
    op.drop_index(op.f("ix_classes_code_invitation"), table_name="classes")
    op.drop_index(op.f("ix_classes_professeur_id"), table_name="classes")
    op.drop_index(op.f("ix_classes_id"), table_name="classes")
    op.drop_table("classes")
