"""Owner: B. Ledger, promotion, radar lamps, overload, escalation
(SIG-1..5, plan.md P2/P3/P4).
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from evermind.contracts.enums import SignalKind, SignalStatus
from evermind.org.service import OrgService
from evermind.signals import promotion
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

    def try_promote(self, *, project_id: int, normalized_topic: str,
                     task_id: int | None = None, party_id: int | None = None,
                     now: datetime | None = None) -> promotion.PromotionDecision | None:
        """SIG-1 promotion. Evaluates the pure rule (`signals.promotion.evaluate`
        — >=2 corroborating, or 1 + staleness) against every open signal for
        this identity; returns the `PromotionDecision` that WOULD be submitted,
        or None if not (yet) eligible.

        Actually submitting it — a `RecordSignal` command through
        `decisions.service.handle` (never a direct write to `tasks.blocked_*`,
        architecture.md: signals "must NOT ... mutate tasks; it proposes via
        commands") — is blocked on DEC-1..9 existing (Lane A, still
        NotImplementedError); wire that call here once it does.
        """
        open_signals = self.open_signals_for_identity(
            project_id=project_id, normalized_topic=normalized_topic,
            task_id=task_id, party_id=party_id,
        )
        return promotion.evaluate(open_signals, now=now or datetime.now(timezone.utc))

    def resolve_waiting_on(self, text: str) -> dict:
        """SIG-2 — `waiting_on` resolution: fuzzy-match `text` against known
        `parties` via `org.service` (signals IS on org's read-port allowlist,
        architecture.md), else keep the free text (G22). `org.service.
        match_party_alias` doesn't exist yet (Lane A) — this call will raise
        NotImplementedError until it does; the fallback-to-text branch below
        is what SIG-2 actually promises when no match is found.
        """
        party = OrgService(self.session).match_party_alias(text)
        if party is not None:
            return {"party_id": party.id}
        return {"waiting_on_text": text}

    def radar_sweep(self) -> list[dict]:
        """TODO(B, P4): SIG-3 daily job — flush-before-read, then lamps: blocked/
        at-risk/overdue/stale/idle/late-start/contested. Reads `tasks.service`
        (read port)."""
        raise NotImplementedError

    def overload_for(self, user_id: int) -> dict:
        """TODO(B, P6): SIG-4 — per-day concurrent load, next 14 days,
        warn-don't-block."""
        raise NotImplementedError
