"""Small persistence helpers shared by decision command handlers."""

from __future__ import annotations

from hashlib import sha256

from sqlalchemy import or_, select, text
from sqlalchemy.orm import Session
from sqlalchemy.sql.elements import ColumnElement

from evermind.db.eventlog import DomainEvent
from evermind.decisions.facets import DerivedUnit, version_for_bindings
from evermind.decisions.models import EffectiveUnit
from evermind.decisions.ordering import HandleContext


def target_lock_id(target: str) -> int:
    return int.from_bytes(sha256(target.encode()).digest()[:8], signed=True)


def serialize_targets(session: Session, targets: set[str]) -> None:
    for target in sorted(targets):
        session.execute(
            text("SELECT pg_advisory_xact_lock(:lock_id)"),
            {"lock_id": target_lock_id(target)},
        )


def append_event(
    session: Session,
    *,
    context: HandleContext,
    kind: str,
    aggregate: str,
    aggregate_id: int,
    payload: dict,
    command_id: str,
) -> DomainEvent:
    event = DomainEvent(
        ts=context.event_ts,
        kind=kind,
        aggregate=aggregate,
        aggregate_id=aggregate_id,
        payload=payload,
        caused_by_command=command_id,
    )
    session.add(event)
    session.flush()
    return event


def current_bindings(session: Session, unit_keys: set[str]) -> dict[str, int]:
    if not unit_keys:
        return {}
    rows = session.execute(
        select(EffectiveUnit.unit_key, EffectiveUnit.decision_id).where(
            EffectiveUnit.unit_key.in_(unit_keys)
        )
    ).all()
    return {row[0]: row[1] for row in rows}


def current_bindings_for_units(
    session: Session,
    units: list[DerivedUnit],
) -> dict[str, int]:
    unit_keys = {unit.unit_key for unit in units if unit.occupies}
    prefixes = {
        unit.conflict_prefix for unit in units if unit.occupies and unit.conflict_prefix is not None
    }
    conditions: list[ColumnElement[bool]] = (
        [EffectiveUnit.unit_key.in_(unit_keys)] if unit_keys else []
    )
    conditions.extend(EffectiveUnit.unit_key.startswith(prefix) for prefix in prefixes)
    if not conditions:
        return {}
    rows = session.execute(
        select(EffectiveUnit.unit_key, EffectiveUnit.decision_id).where(or_(*conditions))
    ).all()
    return {row[0]: row[1] for row in rows}


def current_version(session: Session, unit_keys: set[str]) -> str:
    return version_for_bindings(current_bindings(session, unit_keys))
