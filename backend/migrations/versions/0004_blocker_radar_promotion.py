"""add retained evidence and promotion linkage to signals

Revision ID: 0004_blocker_radar_promotion
Revises: 0003_decision_task_context
"""
from alembic import op
import sqlalchemy as sa

revision = "0004_blocker_radar_promotion"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("signals", sa.Column("evidence", sa.JSON(), nullable=False,
                                       server_default=sa.text("'[]'")))
    op.add_column("signals", sa.Column("promoted_decision_id", sa.Integer(), nullable=True))
    op.add_column("decisions", sa.Column("review_reason", sa.String(), nullable=True))
    op.add_column("decisions", sa.Column("reported_by_user_id", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("signals", "promoted_decision_id")
    op.drop_column("signals", "evidence")
    op.drop_column("decisions", "reported_by_user_id")
    op.drop_column("decisions", "review_reason")
