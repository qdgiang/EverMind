from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from evermind.contracts.commands import ApproveProposal, OpSpec, ProposeDecision
from evermind.contracts.enums import CreatedFrom, DecisionScope, DecisionStatus
from evermind.decisions.models import Decision, EffectiveUnit
from evermind.decisions.service import DecisionsService
from tests.scenarios.test_lifecycle_basics import FakeTaskStatePort, _context, _seed_org


def _window_command(
    *,
    command_id: str,
    value: str,
    effect_window: tuple[datetime, datetime] | None,
) -> ProposeDecision:
    return ProposeDecision(
        client_command_id=UUID(command_id),
        persona="joe",
        created_from=CreatedFrom.DASHBOARD,
        decided_by_user_id=302,
        scope=DecisionScope.TASK,
        scope_target="task:501",
        description=f"Use venue {value}",
        ops=[OpSpec(target="task:501", facet="attr:venue", op="set", value=value)],
        effect_window=effect_window,
        citations=[],
    )


def test_windowed_exception_shadows_without_displacing_and_overlap_holds(
    db_session: Session,
) -> None:
    """S17/G42/EVM-004: exceptions shadow standing truth; overlap never auto-wins."""
    _seed_org(db_session)
    service = DecisionsService(db_session, task_state=FakeTaskStatePort())
    standing = service.handle(
        _window_command(
            command_id="00000000-0000-0000-0000-000000000051",
            value="hall-a",
            effect_window=None,
        ),
        context=_context(event_id="evt-standing-window", hour=8),
    )
    exception = service.handle(
        _window_command(
            command_id="00000000-0000-0000-0000-000000000052",
            value="gym",
            effect_window=(
                datetime(2026, 11, 20, 0, 0),
                datetime(2026, 11, 21, 0, 0),
            ),
        ),
        context=_context(event_id="evt-window-1", hour=9),
    )
    overlapping = service.handle(
        _window_command(
            command_id="00000000-0000-0000-0000-000000000053",
            value="courtyard",
            effect_window=(
                datetime(2026, 11, 20, 12, 0),
                datetime(2026, 11, 22, 0, 0),
            ),
        ),
        context=_context(event_id="evt-window-overlap", hour=10),
    )
    later_exception = service.handle(
        _window_command(
            command_id="00000000-0000-0000-0000-000000000054",
            value="hall-b",
            effect_window=(
                datetime(2026, 11, 22, 0, 0),
                datetime(2026, 11, 23, 0, 0),
            ),
        ),
        context=_context(event_id="evt-window-2", hour=11),
    )

    standing_row = db_session.get(Decision, standing["decision_id"])
    exception_row = db_session.get(Decision, exception["decision_id"])
    overlap_row = db_session.get(Decision, overlapping["decision_id"])
    unit = db_session.scalar(select(EffectiveUnit))
    assert exception["status"] == "effective"
    assert overlapping["status"] == "proposed"
    assert overlapping["hold_reason"] == "window_overlap"
    assert later_exception["status"] == "effective"
    assert standing_row.status is DecisionStatus.EFFECTIVE
    assert exception_row.status is DecisionStatus.EFFECTIVE
    assert overlap_row.status is DecisionStatus.PROPOSED
    assert unit.decision_id == standing_row.id
    unit_key = unit.unit_key
    assert service.effective_decision_id(unit_key, at=datetime(2026, 11, 19, 12, 0)) == (
        standing_row.id
    )
    assert service.effective_decision_id(unit_key, at=datetime(2026, 11, 20, 12, 0)) == (
        exception_row.id
    )
    assert service.effective_decision_id(unit_key, at=datetime(2026, 11, 21, 12, 0)) == (
        standing_row.id
    )

    still_held = service.handle(
        ApproveProposal(
            client_command_id=UUID("00000000-0000-0000-0000-000000000055"),
            persona="joe",
            expected_version=overlapping["version"],
            created_from=CreatedFrom.DASHBOARD,
            decision_id=overlapping["decision_id"],
            approved_by_user_id=302,
        ),
        context=_context(event_id="evt-window-approve", hour=12),
    )
    assert still_held == {
        "ok": False,
        "status": "window_overlap",
        "http_status": 409,
        "decision_id": overlapping["decision_id"],
    }
    assert overlap_row.status is DecisionStatus.PROPOSED
