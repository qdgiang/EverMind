from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.orm import Session


def test_effective_units_allows_one_multiop_decision_to_occupy_multiple_units(
    db_session: Session,
) -> None:
    """EVM-003: decision_id is intentionally non-unique in effective_units."""
    decision_id_unique = db_session.execute(
        text(
            """
            SELECT EXISTS (
                SELECT 1
                FROM pg_constraint c
                JOIN pg_class t ON t.oid = c.conrelid
                WHERE t.relname = 'effective_units'
                  AND c.contype = 'u'
                  AND pg_get_constraintdef(c.oid) = 'UNIQUE (decision_id)'
            )
            """
        )
    ).scalar_one()

    assert decision_id_unique is False
