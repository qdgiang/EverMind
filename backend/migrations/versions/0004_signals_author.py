"""signals: author_user_id (signals-promotion pipeline)

Revision ID: 0004
Revises: 0003
Create Date: 2026-07-19

Additive + idempotent (same IF NOT EXISTS pattern as 0002): fresh DBs already
get the column via 0001's create_all over live models; existing DBs gain it
here without a reset.
"""
from __future__ import annotations

from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE signals ADD COLUMN IF NOT EXISTS author_user_id INTEGER")


def downgrade() -> None:
    op.execute("ALTER TABLE signals DROP COLUMN IF EXISTS author_user_id")
