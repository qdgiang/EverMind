from __future__ import annotations

from uuid import UUID

import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from evermind.contracts.commands import CitationSpec, OpSpec, ProposeDecision
from evermind.contracts.enums import CitationKind, CreatedFrom, DecisionScope, DecisionStatus
from evermind.db.eventlog import DomainEvent
from evermind.decisions.models import Decision, ProcessedCommand
from evermind.decisions.service import DecisionsService
from tests.scenarios.test_lifecycle_basics import (
    FakeTaskStatePort,
    _context,
    _propose,
    _seed_org,
)


def test_llm_provenance_is_rejected_before_any_state_or_event(db_session: Session) -> None:
    """Invariant #10: LLM decisions require source, window, confidence, and citation."""
    _seed_org(db_session)
    service = DecisionsService(db_session, task_state=FakeTaskStatePort())
    outcome = service.handle(
        ProposeDecision(
            client_command_id=UUID("00000000-0000-0000-0000-000000000121"),
            persona="joe",
            created_from=CreatedFrom.LLM,
            source_message_id=8501,
            confidence=0.9,
            decided_by_user_id=302,
            scope=DecisionScope.TASK,
            scope_target="task:501",
            description="Missing extraction window",
            ops=[OpSpec(target="task:501", facet="attr:venue", op="set", value="A")],
            citations=[
                CitationSpec(
                    message_id=8501,
                    kind=CitationKind.EVIDENCE,
                    rev_at_capture=1,
                )
            ],
        ),
        context=_context(
            event_id="evt-missing-window",
            hour=9,
            citation_authors={8501: 302},
        ),
    )

    assert outcome == {
        "ok": False,
        "status": "invalid",
        "http_status": 422,
        "error": "LLM decisions require source_message_id, window_id, and confidence",
    }
    assert db_session.scalar(select(func.count()).select_from(Decision)) == 0
    assert db_session.scalar(select(func.count()).select_from(DomainEvent)) == 0
    assert db_session.scalar(select(func.count()).select_from(ProcessedCommand)) == 0


def test_decision_body_trigger_rejects_op_rewrites_but_allows_lifecycle_flip(
    db_session: Session,
) -> None:
    """Invariant #4/settled #2: bodies are append-only while lifecycle fields stay mutable."""
    _seed_org(db_session)
    service = DecisionsService(db_session, task_state=FakeTaskStatePort())
    outcome = service.handle(
        _propose(
            command_id="00000000-0000-0000-0000-000000000122",
            persona="joe",
            actor=302,
            value="apples",
        ),
        context=_context(event_id="evt-append-only", hour=10),
    )
    decision = db_session.get(Decision, outcome["decision_id"])

    with pytest.raises(DBAPIError, match="append-only"):
        with db_session.begin_nested():
            decision.ops = [
                {"target": "task:501", "facet": "attr:fruit", "op": "set", "value": "pear"}
            ]
            db_session.flush()

    db_session.refresh(decision)
    decision.status = DecisionStatus.REJECTED
    db_session.flush()
    assert decision.status is DecisionStatus.REJECTED
    decision.status = DecisionStatus.EFFECTIVE
    db_session.flush()


def test_decision_schema_has_no_clock_driven_expiry_surface() -> None:
    """Invariant #7/#18: no deadline, TTL, or expired decision status exists."""
    column_names = set(Decision.__table__.columns.keys())
    assert not column_names.intersection({"ttl", "expires_at", "approval_deadline"})
    assert "expired" not in {status.value for status in DecisionStatus}
