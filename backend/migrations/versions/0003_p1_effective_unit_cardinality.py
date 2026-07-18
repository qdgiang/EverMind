"""Allow a multi-operation decision to occupy several effective units.

Revision ID: 0003
Revises: 0002
"""

from __future__ import annotations

from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Revision 0001 creates tables from current metadata, so fresh installs do
    # not have the legacy constraint. Deployed P0 databases still do.
    op.execute(
        "ALTER TABLE effective_units DROP CONSTRAINT IF EXISTS effective_units_decision_id_key"
    )


def downgrade() -> None:
    op.create_unique_constraint(
        "effective_units_decision_id_key",
        "effective_units",
        ["decision_id"],
    )
