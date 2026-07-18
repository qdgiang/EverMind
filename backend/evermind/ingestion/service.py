"""Owner: A. Windows, markers, hydration, extraction, linkage, signals-emit."""
from __future__ import annotations

import re
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from evermind.connectors.models import Message
from evermind.contracts.commands import CitationSpec, OpSpec, ProposeDecision
from evermind.contracts.enums import CitationKind, CreatedFrom, DecisionScope
from evermind.decisions.service import DecisionsService
from evermind.ingestion.models import Materialization
from evermind.org.models import ChatGroup
from evermind.org.service import OrgService
from evermind.tasks.consumer import TasksConsumer
from evermind.tasks.service import TasksService


_MARKER_RE = re.compile(r"^!(decision|blocked)\b\s*[—-]?\s*(.+)$", re.IGNORECASE)

class IngestionService:
    def __init__(self, session: Session):
        self.session = session

    def run_window(self, group_id: int) -> None:
        """TODO(A): ING-2 windowing + ING-3 hydration + ING-4 extraction + ING-5 linkage.
        Reads messages via `connectors.service.ConnectorsService.read_window` (B's read
        port — work-split.md interface #1), never `connectors.models` directly.
        """
        raise NotImplementedError

    def apply_markers(self, message_id: int) -> list[dict]:
        """Materialize a supported marker exactly once through the command gate.

        Marker text is intentionally narrow: the marker itself supplies a
        task description, while richer linkage remains the later window lane.
        """
        message = self.session.get(Message, message_id)
        if message is None:
            raise LookupError(f"message {message_id} not found")
        match = _MARKER_RE.match(message.text.strip())
        if match is None:
            return []

        marker_kind, description = match.groups()
        existing = self.session.scalar(select(Materialization).where(
            Materialization.source_message_id == message.id,
            Materialization.command_index == 0,
            Materialization.kind == marker_kind.lower(),
            Materialization.unit_key == "NEW_TASK|description",
        ))
        if existing is not None:
            return [{"status": "already_materialized", "decision_id": existing.decision_id}]
        if message.group_id is None:
            return [{"status": "unrouted", "reason": "marker source has no chat group"}]

        group = self.session.get(ChatGroup, message.group_id)
        user = OrgService(self.session).get_user_by_handle(message.author_identity)
        if group is None or user is None:
            return [{"status": "unresolved_author", "reason": message.author_identity}]

        ops = [OpSpec(target="NEW_TASK", facet="description", op="set", value=description)]
        if marker_kind.lower() == "blocked":
            ops.append(OpSpec(target="NEW_TASK", facet="status", op="set", value="blocked"))
        command = ProposeDecision(
            client_command_id=uuid4(), persona=user.handle or message.author_identity,
            created_from=CreatedFrom.MARKER, confidence=1.0, ts=message.ts,
            source_message_id=message.id, decided_by_user_id=user.id,
            scope=DecisionScope.TASK, scope_target="NEW_TASK", description=description,
            ops=ops, context_group_id=group.id,
            citations=[CitationSpec(message_id=message.id, kind=CitationKind.EVIDENCE,
                                    rev_at_capture=message.current_rev)],
        )
        outcome = DecisionsService(
            self.session, task_port=TasksService(self.session)
        ).handle(command, commit=False)
        if outcome.get("decision_id") is None and outcome.get("update_id") is None:
            self.session.rollback()
            return [outcome]
        self.session.add(Materialization(
            source_message_id=message.id, command_index=0, kind=marker_kind.lower(),
            unit_key="NEW_TASK|description", decision_id=outcome.get("decision_id"), update_id=None,
        ))
        TasksConsumer(self.session).poll_and_apply()
        self.session.commit()
        return [outcome]

    def on_transcript_uploaded(self, upload_id: int) -> list[dict]:
        """Report an honest result until the non-marker transcript lane lands.

        Transcript messages carry no deterministic marker contract, so claiming
        they were extracted would be false. The upload remains durable and is
        explicitly surfaced as pending the window/LLM extractor.
        """
        return [{"status": "stored_pending_extraction", "upload_id": upload_id}]
