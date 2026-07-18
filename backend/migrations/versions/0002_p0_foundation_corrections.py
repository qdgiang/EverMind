"""P0 foundation corrections.

Revision ID: 0002
Revises: 0001
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None

_TRIGGER = """
CREATE TRIGGER decisions_append_only
BEFORE UPDATE ON decisions
FOR EACH ROW EXECUTE FUNCTION evermind_decisions_append_only();
"""

_CORRECTED_FUNCTION = """
CREATE OR REPLACE FUNCTION evermind_decisions_append_only() RETURNS trigger AS $$
BEGIN
    IF NEW.ts IS DISTINCT FROM OLD.ts
       OR NEW.decided_by_user_id IS DISTINCT FROM OLD.decided_by_user_id
       OR NEW.decided_by_role_at_time IS DISTINCT FROM OLD.decided_by_role_at_time
       OR NEW.scope IS DISTINCT FROM OLD.scope
       OR NEW.scope_target IS DISTINCT FROM OLD.scope_target
       OR NEW.description IS DISTINCT FROM OLD.description
       OR NEW.context IS DISTINCT FROM OLD.context
       OR NEW.ops::text IS DISTINCT FROM OLD.ops::text
       OR NEW.effect_window_from IS DISTINCT FROM OLD.effect_window_from
       OR NEW.effect_window_until IS DISTINCT FROM OLD.effect_window_until
       OR NEW.created_from IS DISTINCT FROM OLD.created_from
       OR NEW.confidence IS DISTINCT FROM OLD.confidence THEN
        RAISE EXCEPTION 'decisions body columns are append-only (settled #2)';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
"""

_REVISION_0001_FUNCTION = """
CREATE OR REPLACE FUNCTION evermind_decisions_append_only() RETURNS trigger AS $$
BEGIN
    IF NEW.ts <> OLD.ts OR NEW.decided_by_user_id <> OLD.decided_by_user_id
       OR NEW.scope <> OLD.scope OR NEW.scope_target <> OLD.scope_target
       OR NEW.description <> OLD.description OR NEW.ops::text <> OLD.ops::text
       OR NEW.created_from <> OLD.created_from THEN
        RAISE EXCEPTION 'decisions body columns are append-only (settled #2)';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
"""


def _replace_append_only_trigger(function_sql: str) -> None:
    op.execute("DROP TRIGGER IF EXISTS decisions_append_only ON decisions")
    op.execute(function_sql)
    op.execute(_TRIGGER)


def upgrade() -> None:
    op.alter_column(
        "projects",
        "end_date",
        existing_type=sa.DateTime(),
        type_=sa.Date(),
        existing_nullable=True,
        postgresql_using="end_date::date",
    )
    _replace_append_only_trigger(_CORRECTED_FUNCTION)


def downgrade() -> None:
    _replace_append_only_trigger(_REVISION_0001_FUNCTION)
    op.alter_column(
        "projects",
        "end_date",
        existing_type=sa.Date(),
        type_=sa.DateTime(),
        existing_nullable=True,
        postgresql_using="end_date::timestamp",
    )
