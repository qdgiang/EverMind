from __future__ import annotations

import os
from importlib import import_module
from uuid import UUID

from sqlalchemy import create_engine, func, select, text
from sqlalchemy.orm import Session

from evermind.contracts.commands import ApproveProposal, OpSpec, ProposeDecision
from evermind.contracts.enums import CreatedFrom, DecisionScope, DecisionStatus
from evermind.db.eventlog import DomainEvent
from evermind.decisions.models import Decision, EffectiveUnit, ProcessedCommand
from evermind.decisions.service import DecisionsService
from tests.scenarios.test_lifecycle_basics import FakeTaskStatePort, _context, _seed_org


def _multiop(
    command_id: str,
    *,
    actor: int,
    persona: str,
    ops: list[OpSpec],
    expected_version: str | None = None,
) -> ProposeDecision:
    return ProposeDecision(
        client_command_id=UUID(command_id),
        persona=persona,
        expected_version=expected_version,
        created_from=CreatedFrom.DASHBOARD,
        decided_by_user_id=actor,
        scope=DecisionScope.TASK,
        scope_target="task:501",
        description="Atomic decision",
        ops=ops,
        citations=[],
    )


def test_multiop_decision_occupies_every_unit_as_one_atomic_row(db_session: Session) -> None:
    """EVM-003: one authorized decision occupies multiple units all-or-nothing."""
    _seed_org(db_session)
    service = DecisionsService(db_session, task_state=FakeTaskStatePort())
    outcome = service.handle(
        _multiop(
            "00000000-0000-0000-0000-000000000081",
            actor=302,
            persona="joe",
            ops=[
                OpSpec(target="task:501", facet="attr:fruit", op="set", value="peach"),
                OpSpec(target="task:501", facet="attr:budget", op="set", value=300),
            ],
        ),
        context=_context(event_id="evt-multi", hour=9),
    )

    units = list(db_session.scalars(select(EffectiveUnit).order_by(EffectiveUnit.unit_key)))
    assert outcome["status"] == "effective"
    assert len(units) == 2
    assert {unit.decision_id for unit in units} == {outcome["decision_id"]}


def test_multiop_routes_to_highest_authority_and_changes_nothing_until_approval(
    db_session: Session,
) -> None:
    """EVM-003: one project-level op holds the whole task+project operation bundle."""
    _seed_org(db_session)
    service = DecisionsService(db_session, task_state=FakeTaskStatePort())
    standing = service.handle(
        _multiop(
            "00000000-0000-0000-0000-000000000082",
            actor=302,
            persona="joe",
            ops=[OpSpec(target="task:501", facet="attr:fruit", op="set", value="apple")],
        ),
        context=_context(event_id="evt-before-multi", hour=9),
    )
    held = service.handle(
        _multiop(
            "00000000-0000-0000-0000-000000000083",
            actor=302,
            persona="joe",
            expected_version=standing["version"],
            ops=[
                OpSpec(target="task:501", facet="attr:fruit", op="set", value="peach"),
                OpSpec(
                    target="project:101",
                    facet="attr:donation-method",
                    op="set",
                    value="VietQR",
                ),
            ],
        ),
        context=_context(event_id="evt-held-multi", hour=10),
    )
    assert held["status"] == "proposed"
    assert db_session.get(Decision, standing["decision_id"]).status is DecisionStatus.EFFECTIVE
    assert db_session.get(EffectiveUnit, "v1|project:101|attr:donation-method") is None

    approved = service.handle(
        ApproveProposal(
            client_command_id=UUID("00000000-0000-0000-0000-000000000084"),
            persona="an",
            expected_version=held["version"],
            created_from=CreatedFrom.DASHBOARD,
            decision_id=held["decision_id"],
            approved_by_user_id=301,
        ),
        context=_context(event_id="evt-approved-multi", hour=11),
    )
    assert approved["status"] == "effective"
    assert db_session.get(Decision, standing["decision_id"]).status is DecisionStatus.SUPERSEDED
    assert {unit.decision_id for unit in db_session.scalars(select(EffectiveUnit))} == {
        held["decision_id"]
    }


def test_invalid_multiop_returns_deterministic_error_with_no_partial_rows_or_events(
    db_session: Session,
) -> None:
    """EVM-003: one invalid op rejects the whole command without a receipt or event."""
    _seed_org(db_session)
    service = DecisionsService(db_session, task_state=FakeTaskStatePort())
    outcome = service.handle(
        _multiop(
            "00000000-0000-0000-0000-000000000085",
            actor=302,
            persona="joe",
            ops=[
                OpSpec(target="task:501", facet="attr:fruit", op="set", value="peach"),
                OpSpec(target="task:501", facet="status", op="append", value="done"),
            ],
        ),
        context=_context(event_id="evt-invalid-multi", hour=12),
    )

    assert outcome == {
        "ok": False,
        "status": "invalid",
        "http_status": 422,
        "error": "unsupported op 'append' for facet 'status'",
    }
    assert db_session.scalar(select(func.count()).select_from(Decision)) == 0
    assert db_session.scalar(select(func.count()).select_from(EffectiveUnit)) == 0
    assert db_session.scalar(select(func.count()).select_from(DomainEvent)) == 0
    assert db_session.scalar(select(func.count()).select_from(ProcessedCommand)) == 0


def test_effective_writes_hold_transaction_scoped_locks_for_every_target(
    db_session: Session,
) -> None:
    """DEC-3: concurrent effective writes serialize per target in PostgreSQL."""
    _seed_org(db_session)
    service = DecisionsService(db_session, task_state=FakeTaskStatePort())
    service.handle(
        _multiop(
            "00000000-0000-0000-0000-000000000086",
            actor=302,
            persona="joe",
            ops=[OpSpec(target="task:501", facet="attr:fruit", op="set", value="peach")],
        ),
        context=_context(event_id="evt-lock", hour=13),
    )
    persistence = import_module("evermind.decisions.persistence")
    lock_id = persistence.target_lock_id("task:501")
    other_engine = create_engine(os.environ["DATABASE_URL"])
    with other_engine.begin() as connection:
        acquired = connection.execute(
            text("SELECT pg_try_advisory_xact_lock(:lock_id)"),
            {"lock_id": lock_id},
        ).scalar_one()
    other_engine.dispose()

    assert acquired is False
