"""decisions plumbing: decision_units + id_allocations + full append-only trigger

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-18

Owner: A (`decisions` tables — architecture.md: after 0001 each owner migrates
their own tables; the gate renumbers on merge collisions).

- `decision_units`: every unit a decision's ops touch (proposed included) —
  powers the sweep (G11/G12), pending-merge (G49), #17b withdrawal, and the
  [EVM-004] overlap check without parsing ops JSON in SQL.
- `id_allocations`: task-id allocator for NEW_TASK decisions (the fold creates
  the task row from the event payload; identity is minted on the write side).
- replaces the 0001 append-only trigger function with FULL body-column coverage
  (settled #2 / data-model invariant #4): adds decided_by_role_at_time, context,
  effect_window, confidence, scope, recorded_at, window_id, stable_event_id.
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # a multi-op decision occupies several units at once [EVM-003] — the 0001
    # scaffold's UNIQUE(decision_id) on effective_units was wrong
    op.execute("ALTER TABLE effective_units "
               "DROP CONSTRAINT IF EXISTS effective_units_decision_id_key")
    op.create_table(
        "decision_units",
        sa.Column("decision_id", sa.Integer, sa.ForeignKey("decisions.id"),
                  primary_key=True),
        sa.Column("unit_key", sa.String, primary_key=True),
        if_not_exists=True,
    )
    op.create_index("ix_decision_units_unit_key", "decision_units", ["unit_key"],
                    if_not_exists=True)
    op.create_table(
        "id_allocations",
        sa.Column("name", sa.String, primary_key=True),
        sa.Column("next_id", sa.Integer, nullable=False, server_default="1"),
        if_not_exists=True,
    )
    op.execute(
        """
        CREATE OR REPLACE FUNCTION evermind_decisions_append_only() RETURNS trigger AS $$
        BEGIN
            IF NEW.ts IS DISTINCT FROM OLD.ts
               OR NEW.recorded_at IS DISTINCT FROM OLD.recorded_at
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
               OR NEW.confidence IS DISTINCT FROM OLD.confidence
               OR NEW.window_id IS DISTINCT FROM OLD.window_id
               OR NEW.stable_event_id IS DISTINCT FROM OLD.stable_event_id THEN
                RAISE EXCEPTION 'decisions body columns are append-only (settled #2)';
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )


def downgrade() -> None:
    # restore the 0001 (partial-coverage) trigger function
    op.execute(
        """
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
    )
    op.drop_index("ix_decision_units_unit_key", "decision_units")
    op.drop_table("id_allocations")
    op.drop_table("decision_units")
