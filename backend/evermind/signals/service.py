"""Owner: B. Ledger, promotion, radar lamps, overload, escalation
(SIG-1..5, plan.md P2/P3/P4).

P2 (this file, so far): SIG-1 ledger emit only — every mention is appended,
never deduped or merged at write time; promotion (P3) is what counts
accumulated mentions per identity and decides whether to propose a `blocked`
state or a `requested` dependency edge.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from evermind.contracts.enums import SignalKind, SignalStatus
from evermind.signals.models import Signal


class SignalsService:
    def __init__(self, session: Session):
        self.session = session

    def emit(self, *, kind: SignalKind, project_id: int, normalized_topic: str, excerpt: str,
              message_id: int, ts: datetime, window_id: int, task_id: int | None = None,
              party_id: int | None = None) -> int:
        """SIG-1 — append-only ledger row keyed on the [EVM-013] identity
        (project, task?, party?, normalized_topic). Does NOT auto-promote —
        "one mention never promotes" (design-v2.md §Signals). Returns the new
        signal's id.
        """
        signal = Signal(
            kind=kind, project_id=project_id, task_id=task_id, party_id=party_id,
            normalized_topic=normalized_topic, excerpt=excerpt, message_id=message_id,
            ts=ts, window_id=window_id, status=SignalStatus.OPEN,
        )
        self.session.add(signal)
        self.session.flush()
        return signal.id

    def open_signals_for_identity(self, *, project_id: int, normalized_topic: str,
                                    task_id: int | None = None,
                                    party_id: int | None = None) -> list[Signal]:
        """All accumulated open mentions for one [EVM-013] identity — the input
        to P3's promotion rule (>=2 corroborating, or 1 + staleness).
        """
        stmt = (
            select(Signal)
            .where(Signal.project_id == project_id)
            .where(Signal.normalized_topic == normalized_topic)
            .where(Signal.task_id == task_id)
            .where(Signal.party_id == party_id)
            .where(Signal.status == SignalStatus.OPEN)
            .order_by(Signal.ts)
        )
        return list(self.session.scalars(stmt))

    def try_promote(self, project_id: int, normalized_topic: str) -> None:
        """TODO(B, P3): SIG-1 promotion — >=2 corroborating signals, or 1 +
        staleness, emits a `RecordSignal`/proposed-blocked command via
        `decisions.service` (never writes tasks.blocked_* directly)."""
        raise NotImplementedError

    def radar_sweep(self) -> list[dict]:
        """TODO(B, P4): SIG-3 daily job — flush-before-read, then lamps: blocked/
        at-risk/overdue/stale/idle/late-start/contested. Reads `tasks.service`
        (read port)."""
        raise NotImplementedError

    def overload_for(self, user_id: int) -> dict:
        """TODO(B, P6): SIG-4 — per-day concurrent load, next 14 days,
        warn-don't-block."""
        raise NotImplementedError
