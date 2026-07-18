"""Recorded marker path: source message -> command -> task projection."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from evermind.connectors.models import Message
from evermind.ingestion.models import Materialization
from evermind.ingestion.service import IngestionService
from evermind.tasks.models import Task


def test_authorized_decision_marker_materializes_once_and_projects_a_task(db_session, org_ids):
    message = Message(
        id=9001, source="replay", group_id=org_ids["groups"]["G-TT"], author_identity="linh",
        ts=datetime.now(timezone.utc) + timedelta(days=30),
        text="!decision Confirm the sound-check plan", thread_ref=None,
        raw_ref="test:9001", kind="text",
    )
    db_session.add(message)
    db_session.flush()

    first = IngestionService(db_session).apply_markers(message.id)
    second = IngestionService(db_session).apply_markers(message.id)

    assert first[0]["status"] == "effective"
    assert second[0]["status"] == "already_materialized"
    assert db_session.scalar(select(Task).where(Task.description == "Confirm the sound-check plan"))
    assert len(list(db_session.scalars(select(Materialization)))) == 1
