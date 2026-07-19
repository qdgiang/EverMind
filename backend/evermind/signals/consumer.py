"""Owner: B. The signals event-consumer — D3 read side, mirror of
`tasks/consumer.py`. `decisions` (A) appends `signal_recorded` events; this
folds them into the weak-signal ledger (`signals` table) and never writes
anything else. Tracks its own position via `ProjectionOffset`
(consumer="signals").

The ledger is APPEND-per-mention (SIG-1): one row per voiced mention keyed on
the [EVM-013] identity — promotion (`signals/service.py:promotion_sweep`) is a
separate beat that reads what accumulated here.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from evermind.contracts.enums import SignalKind, SignalStatus
from evermind.db.eventlog import DomainEvent, ProjectionOffset
from evermind.signals.models import Signal

CONSUMER_NAME = "signals"


class SignalsConsumer:
    def __init__(self, session: Session):
        self.session = session

    def _offset(self) -> ProjectionOffset:
        offset = self.session.get(ProjectionOffset, CONSUMER_NAME)
        if offset is None:
            offset = ProjectionOffset(consumer=CONSUMER_NAME, last_seq=0)
            self.session.add(offset)
            self.session.flush()
        return offset

    def poll_and_apply(self) -> int:
        offset = self._offset()
        events = self.session.scalars(
            select(DomainEvent)
            .where(DomainEvent.seq > offset.last_seq)
            .order_by(DomainEvent.seq)
        ).all()
        applied = 0
        for event in events:
            if event.kind == "signal_recorded":
                self._on_signal_recorded(event)
                applied += 1
            offset.last_seq = event.seq
        return applied

    def _on_signal_recorded(self, event: DomainEvent) -> None:
        p = event.payload
        ts = datetime.fromisoformat(p["ts"]) if p.get("ts") else event.ts
        self.session.add(Signal(
            kind=SignalKind(p["signal_kind"]),
            project_id=p["project_id"],
            task_id=p.get("task_id"),
            party_id=p.get("party_id"),
            normalized_topic=p["normalized_topic"],
            excerpt=p.get("excerpt", ""),
            message_id=p.get("message_id") or 0,
            ts=ts,
            window_id=p.get("window_id") or 0,
            status=SignalStatus.OPEN,
            author_user_id=p.get("author_user_id"),
        ))
        self.session.flush()
