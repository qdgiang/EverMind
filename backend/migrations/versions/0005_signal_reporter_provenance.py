"""retain reporter provenance in the signal ledger

Revision ID: 0005_signal_reporter_provenance
Revises: 0004_blocker_radar_promotion
"""
from alembic import op
import sqlalchemy as sa

revision = "0005_signal_reporter_provenance"
down_revision = "0004_blocker_radar_promotion"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("signals", sa.Column("reported_by_user_id", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("signals", "reported_by_user_id")
