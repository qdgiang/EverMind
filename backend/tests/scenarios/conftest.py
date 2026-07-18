from __future__ import annotations

import os
from collections.abc import Iterator

import pytest
from sqlalchemy import create_engine, exists, select
from sqlalchemy.orm import Session

from evermind.contracts.enums import CreatedFrom, DecisionStatus
from evermind.decisions.models import Decision, DecisionCitation, EffectiveUnit


@pytest.fixture
def db_session() -> Iterator[Session]:
    engine = create_engine(os.environ["DATABASE_URL"], pool_pre_ping=True)
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, expire_on_commit=False)
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()
        engine.dispose()


@pytest.fixture(autouse=True)
def assert_p1_decision_invariants(db_session: Session) -> Iterator[None]:
    """Sweep durable P1 invariants after every domain scenario end-state."""
    yield
    db_session.flush()
    chat_without_citation = db_session.scalar(
        select(Decision.id)
        .where(
            Decision.created_from.in_([CreatedFrom.MARKER, CreatedFrom.LLM]),
            ~exists().where(DecisionCitation.decision_id == Decision.id),
        )
        .limit(1)
    )
    llm_without_provenance = db_session.scalar(
        select(Decision.id)
        .where(
            Decision.created_from == CreatedFrom.LLM,
            (Decision.window_id.is_(None) | Decision.confidence.is_(None)),
        )
        .limit(1)
    )
    invalid_effective_unit = db_session.scalar(
        select(EffectiveUnit.unit_key)
        .join(Decision, Decision.id == EffectiveUnit.decision_id)
        .where(
            (Decision.status != DecisionStatus.EFFECTIVE) | Decision.effect_window_from.is_not(None)
        )
        .limit(1)
    )
    assert chat_without_citation is None
    assert llm_without_provenance is None
    assert invalid_effective_unit is None
