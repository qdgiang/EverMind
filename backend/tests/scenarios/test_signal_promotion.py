"""L1 — SIG-1 promotion rule + SIG-2 party resolution (plan.md P3 Lane B)."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from evermind.contracts.enums import SignalKind
from evermind.signals import promotion
from evermind.signals.service import SignalsService

T0 = datetime(2026, 9, 1, tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# The pure rule (evaluate) — the actual business value, fully testable
# ---------------------------------------------------------------------------


def test_no_signals_never_promotes():
    assert promotion.evaluate([], now=T0) is None


def test_single_fresh_mention_never_promotes(db_session: Session):
    """X-2 (data-v2 distractor): a single passing remark must NOT fire."""
    SignalsService(db_session).emit(
        kind=SignalKind.BLOCKER, project_id=1, normalized_topic="sound-supplier",
        excerpt="mention", message_id=1, ts=T0, window_id=1,
    )
    open_signals = SignalsService(db_session).open_signals_for_identity(
        project_id=1, normalized_topic="sound-supplier",
    )
    decision = promotion.evaluate(open_signals, now=T0 + timedelta(hours=1))
    assert decision is None


def test_two_corroborating_mentions_promote(db_session: Session):
    """Mirrors B-2: 3 passing mentions, never marked !blocked, still promotes
    once corroborated."""
    service = SignalsService(db_session)
    service.emit(kind=SignalKind.BLOCKER, project_id=1, normalized_topic="sound-supplier",
                 excerpt="mention 1", message_id=10, ts=T0, window_id=1)
    service.emit(kind=SignalKind.BLOCKER, project_id=1, normalized_topic="sound-supplier",
                 excerpt="mention 2", message_id=20, ts=T0 + timedelta(days=2), window_id=2)

    open_signals = service.open_signals_for_identity(
        project_id=1, normalized_topic="sound-supplier",
    )
    decision = promotion.evaluate(open_signals, now=T0 + timedelta(days=2, hours=1))
    assert decision is not None
    assert decision.kind == SignalKind.BLOCKER
    assert decision.citation_message_ids == [10, 20]  # G27: ALL accumulated mentions
    assert decision.since == T0


def test_single_stale_mention_promotes(db_session: Session):
    """design-v2.md: "1 + staleness" also promotes, even without corroboration."""
    SignalsService(db_session).emit(
        kind=SignalKind.BLOCKER, project_id=1, normalized_topic="printer-vendor",
        excerpt="mention", message_id=5, ts=T0, window_id=1,
    )
    open_signals = SignalsService(db_session).open_signals_for_identity(
        project_id=1, normalized_topic="printer-vendor",
    )
    fresh = promotion.evaluate(open_signals, now=T0 + timedelta(days=1))
    stale = promotion.evaluate(open_signals, now=T0 + timedelta(days=8))
    assert fresh is None
    assert stale is not None
    assert stale.citation_message_ids == [5]


# ---------------------------------------------------------------------------
# try_promote — wires the rule against the real ledger
# ---------------------------------------------------------------------------


def test_try_promote_returns_none_when_not_eligible(db_session: Session):
    SignalsService(db_session).emit(
        kind=SignalKind.DEPENDENCY, project_id=1, normalized_topic="vendor-x",
        excerpt="mention", message_id=1, ts=T0, window_id=1,
    )
    result = SignalsService(db_session).try_promote(
        project_id=1, normalized_topic="vendor-x", now=T0 + timedelta(hours=1),
    )
    assert result is None


def test_try_promote_returns_a_decision_when_eligible(db_session: Session):
    service = SignalsService(db_session)
    service.emit(kind=SignalKind.DEPENDENCY, project_id=1, normalized_topic="vendor-x",
                 excerpt="a", message_id=1, ts=T0, window_id=1)
    service.emit(kind=SignalKind.DEPENDENCY, project_id=1, normalized_topic="vendor-x",
                 excerpt="b", message_id=2, ts=T0 + timedelta(hours=1), window_id=1)

    result = service.try_promote(
        project_id=1, normalized_topic="vendor-x", now=T0 + timedelta(hours=2),
    )
    assert result is not None
    assert result.kind == SignalKind.DEPENDENCY
    assert result.citation_message_ids == [1, 2]


# ---------------------------------------------------------------------------
# SIG-2 — party resolution (real match/no-match: org.service landed with PR #42)
# ---------------------------------------------------------------------------


def test_resolve_waiting_on_matches_a_seeded_party_alias(db_session: Session, org_ids):
    """G22/SIG-2 — "đang chờ Kim Long" resolves to the vendor party via alias
    containment (match logic: org.service.match_party_alias, Lane A)."""
    resolved = SignalsService(db_session).resolve_waiting_on("đang chờ Kim Long báo giá")
    assert resolved == {"party_id": org_ids["parties"]["PTY-KL"]}


def test_resolve_waiting_on_keeps_free_text_when_no_party_matches(db_session: Session, org_ids):
    """G22 — no forced match: unknown counterparties stay free text."""
    resolved = SignalsService(db_session).resolve_waiting_on("bên giao hàng mới")
    assert resolved == {"waiting_on_text": "bên giao hàng mới"}
