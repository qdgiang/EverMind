from __future__ import annotations

from datetime import UTC, datetime
from importlib import import_module

import pytest
from sqlalchemy import JSON, text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from evermind.contracts.enums import CreatedFrom, DecisionScope, DecisionStatus
from evermind.db.base import Base
from evermind.decisions.models import Decision


_MODEL_MODULES = (
    "evermind.org.models",
    "evermind.connectors.models",
    "evermind.ingestion.models",
    "evermind.decisions.models",
    "evermind.db.eventlog",
    "evermind.tasks.models",
    "evermind.signals.models",
    "evermind.surfacing.models",
)


def _decision(decision_id: int) -> Decision:
    now = datetime.now(UTC)
    return Decision(
        id=decision_id,
        ts=now,
        recorded_at=now,
        decided_by_user_id=1,
        decided_by_role_at_time=3,
        scope=DecisionScope.PROJECT,
        scope_target="project:1",
        description="Keep the approved venue",
        context=None,
        note=None,
        ops=[{"target": "project:1", "facet": "attr:venue", "op": "set", "value": "A"}],
        effect_window_from=None,
        effect_window_until=None,
        status=DecisionStatus.EFFECTIVE,
        rejected_reason=None,
        supersedes_decision_id=None,
        superseded_by_decision_id=None,
        approved_by_user_id=None,
        approval_via=None,
        approved_by_role_at_act=None,
        created_from=CreatedFrom.DASHBOARD,
        confidence=None,
        window_id=None,
        stable_event_id=f"p0-{decision_id}",
    )


def test_all_model_modules_register_dict_payloads_as_json():
    for module_name in _MODEL_MODULES:
        import_module(module_name)

    assert isinstance(Base.metadata.tables["task_updates"].c.payload.type, JSON)
    assert isinstance(Base.metadata.tables["feed_entries"].c.payload.type, JSON)


def test_project_end_date_is_stored_as_date(db_session: Session):
    data_type = db_session.execute(
        text(
            "SELECT data_type FROM information_schema.columns "
            "WHERE table_schema='public' AND table_name='projects' AND column_name='end_date'"
        )
    ).scalar_one()
    assert data_type == "date"


def test_decision_context_is_immutable_even_when_old_value_is_null(db_session: Session):
    decision = _decision(99001)
    db_session.add(decision)
    db_session.flush()

    with pytest.raises(DBAPIError, match="append-only"):
        with db_session.begin_nested():
            decision.context = "A body rewrite must fail"
            db_session.flush()


def test_decision_status_remains_mutable(db_session: Session):
    decision = _decision(99002)
    db_session.add(decision)
    db_session.flush()
    decision.status = DecisionStatus.SUPERSEDED
    db_session.flush()
    assert decision.status is DecisionStatus.SUPERSEDED
