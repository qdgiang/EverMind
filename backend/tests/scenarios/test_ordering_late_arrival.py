from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from evermind.contracts.commands import OpSpec, ProposeDecision
from evermind.contracts.enums import CreatedFrom, DecisionScope, DecisionStatus
from evermind.decisions.models import Decision, EffectiveUnit
from evermind.decisions.ordering import HandleContext
from evermind.decisions.service import DecisionsService
from tests.scenarios.test_lifecycle_basics import FakeTaskStatePort, _seed_org


def _decision(
    command_id: str,
    value: str,
    *,
    expected_version: str | None = None,
) -> ProposeDecision:
    return ProposeDecision(
        client_command_id=UUID(command_id),
        persona="joe",
        expected_version=expected_version,
        created_from=CreatedFrom.DASHBOARD,
        decided_by_user_id=302,
        scope=DecisionScope.TASK,
        scope_target="task:501",
        description=f"Venue {value}",
        ops=[OpSpec(target="task:501", facet="attr:venue", op="set", value=value)],
        citations=[],
    )


def _ordering_context(
    *,
    event_ts: datetime,
    recorded_at: datetime,
    stable_id: str,
    explicit_supersedes: int | None = None,
) -> HandleContext:
    return HandleContext(
        event_ts=event_ts,
        recorded_at=recorded_at,
        stable_event_id=stable_id,
        explicit_supersedes_decision_id=explicit_supersedes,
    )


def test_late_history_is_born_superseded_and_never_rewinds_current_state(
    db_session: Session,
) -> None:
    """S15/G31/EVM-012: event_ts, recorded_at, then stable id orders birth."""
    _seed_org(db_session)
    service = DecisionsService(db_session, task_state=FakeTaskStatePort())
    current = service.handle(
        _decision("00000000-0000-0000-0000-000000000071", "current"),
        context=_ordering_context(
            event_ts=datetime(2026, 11, 12, 14, 0),
            recorded_at=datetime(2026, 11, 12, 14, 1),
            stable_id="evt-current",
        ),
    )
    late = service.handle(
        _decision(
            "00000000-0000-0000-0000-000000000072",
            "old-history",
            expected_version=current["version"],
        ),
        context=_ordering_context(
            event_ts=datetime(2026, 11, 12, 10, 0),
            recorded_at=datetime(2026, 11, 12, 16, 0),
            stable_id="evt-late",
        ),
    )

    current_row = db_session.get(Decision, current["decision_id"])
    late_row = db_session.get(Decision, late["decision_id"])
    unit = db_session.scalar(select(EffectiveUnit))
    assert late["status"] == "superseded"
    assert late["late_arrival"] is True
    assert late_row.status is DecisionStatus.SUPERSEDED
    assert late_row.superseded_by_decision_id == current_row.id
    assert current_row.status is DecisionStatus.EFFECTIVE
    assert unit.decision_id == current_row.id


def test_impossible_explicit_supersession_routes_to_chronology_hold(
    db_session: Session,
) -> None:
    """ING-7: causal validity wins before timestamp ordering and cannot rewrite history."""
    _seed_org(db_session)
    service = DecisionsService(db_session, task_state=FakeTaskStatePort())
    current = service.handle(
        _decision("00000000-0000-0000-0000-000000000073", "current"),
        context=_ordering_context(
            event_ts=datetime(2026, 11, 12, 14, 0),
            recorded_at=datetime(2026, 11, 12, 14, 1),
            stable_id="evt-current-explicit",
        ),
    )
    impossible = service.handle(
        _decision(
            "00000000-0000-0000-0000-000000000074",
            "claimed-new",
            expected_version=current["version"],
        ),
        context=_ordering_context(
            event_ts=datetime(2026, 11, 12, 10, 0),
            recorded_at=datetime(2026, 11, 12, 16, 0),
            stable_id="evt-impossible",
            explicit_supersedes=current["decision_id"],
        ),
    )

    assert impossible["status"] == "proposed"
    assert impossible["hold_reason"] == "chronology_conflict"
    assert db_session.get(Decision, current["decision_id"]).status is DecisionStatus.EFFECTIVE
